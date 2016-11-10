#!/usr/bin/env python
from __future__ import print_function, division

import ast
import importlib
from pprint import pprint
import sys

import networkx as nx
import numpy as np
from scipy.spatial.distance import pdist, squareform
import scipy.integrate as integrate

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import matplotlib.cm as cmx
import matplotlib.colors as colors
import matplotlib.patches as mpatches

results_name = sys.argv[1]

results = importlib.import_module(results_name)




graph = nx.Graph()
graph.add_nodes_from(range(1, len(results.coords)+1))

# Store the coordinates
for (nid, coord) in enumerate(results.coords, start=1):
    graph.node[nid]['pos'] = coord
    graph.node[nid]['label'] = nid

# Add edges
for (nid, nid_neighbours) in results.neighbours.items():
    graph.add_edges_from((nid, n) for n in nid_neighbours)

def ilp_ndarray_str_eval(il_array):
    il_array = il_array.replace("0 ", "0, ")
    il_array = il_array.replace("1 ", "1, ")
    il_array = il_array.replace("]", "],")

    return ast.literal_eval(il_array[:-1])

attacker_path = ilp_ndarray_str_eval(results.attacker_path)
broadcasts = ilp_ndarray_str_eval(results.broadcasts)

# First of all convert the attacker moves and broadcasts into something sane
attacker_moves_at_time = [results.attacker_edges[moves.index(1)] for moves in attacker_path]
broadcasts_at_time = [set() for _ in attacker_moves_at_time]

for (nid, mess_and_time) in enumerate(broadcasts, start=1):
    for (mess, times) in enumerate(mess_and_time, start=1):
        try:
            time = times.index(1)

            broadcasts_at_time[time].add((nid, mess))
        except ValueError:
            pass

attacker_positions = [v for (u, v) in attacker_moves_at_time]

time_steps = len(attacker_moves_at_time)

def get_cmap(N):
    '''Returns a function that maps each index in 0, 1, ... N-1 to a distinct 
    RGBA color.'''
    color_norm  = colors.Normalize(vmin=0, vmax=N-1)
    scalar_map = cmx.ScalarMappable(norm=color_norm, cmap='hsv') 
    def map_index_to_rgb_color(index):
        return scalar_map.to_rgba(index)
    return map_index_to_rgb_color

colour_map = get_cmap(results.messages)

attacker_colour = "red"
message_colours = [str(colors.rgb2hex(colour_map(i))) for i in range(results.messages)]

#------------------------------------------------------------
# set up figure and animation
fig = plt.gcf()

pos = nx.get_node_attributes(graph, 'pos')

def init():
    global attacker_responded_to
    attacker_responded_to = []

def animate(i):
    global attacker_responded_to
    fig.clf()

    ax = fig.gca()
    
    attacker_at_node = attacker_positions[i]

    # When the attacker is on a node set it to red
    colours = ["w"] * len(results.coords)
    colours[attacker_at_node-1] = attacker_colour

    # Draw circles behind nodes when broadcasting
    for (nid, msg) in broadcasts_at_time[i]:
        c = plt.Circle(results.coords[nid-1], radius=0.25, color=message_colours[msg-1], label=msg)
        ax.add_patch(c)

        if i > 0 and attacker_positions[i] != attacker_positions[i-1] and attacker_at_node == nid:
            attacker_responded_to.append(msg)

    # Draw the graph
    nx.draw(graph, pos, node_size=750, node_color=colours)

    labels = nx.draw_networkx_labels(graph, pos, nx.get_node_attributes(graph, 'label'), font_size=16)

    ax.annotate("Time Step {}, actual time is {:.3f} seconds\nResponded to {} messages".format(i, i/results.slots_per_second, attacker_responded_to), (0.1,-0.4)) # add text

    legend_patches = [mpatches.Patch(color=colour, label='Msg {}'.format(msg)) for (colour, msg) in zip(message_colours, range(1, results.messages+1))]
    lgd = ax.legend(handles=legend_patches, loc=(-0.15,0.2))

ani = animation.FuncAnimation(fig, animate, frames=time_steps,
                              interval=2500, blit=False, init_func=init,
                              repeat=True, repeat_delay=2500)


# save the animation as an mp4.  This requires ffmpeg or mencoder to be
# installed.  The extra_args ensure that the x264 codec is used, so that
# the video can be embedded in html5.  You may need to adjust this for
# your system: for more information, see
# http://matplotlib.sourceforge.net/api/animation_api.html
ani.save('attackerilp.mp4', extra_args=['-vcodec', 'libx264'])
ani.save('attackerilp.gif', writer='imagemagick')

plt.show()