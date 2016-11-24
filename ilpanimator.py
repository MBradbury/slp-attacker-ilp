#!/usr/bin/env python
from __future__ import print_function, division

import ast
import importlib
import sys

import networkx as nx
import numpy as np

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import matplotlib.cm as cmx
import matplotlib.colors as colors
import matplotlib.patches as mpatches

from results.parser import Results

results_name = sys.argv[1]

r = Results(results_name)

def get_cmap(N):
    '''Returns a function that maps each index in 0, 1, ... N-1 to a distinct 
    RGBA color.'''
    color_norm  = colors.Normalize(vmin=0, vmax=N)
    scalar_map = cmx.ScalarMappable(norm=color_norm, cmap='hsv') 
    def map_index_to_rgb_color(index):
        return scalar_map.to_rgba(index)
    return map_index_to_rgb_color

colour_map = get_cmap(r.results.messages)

attacker_colour = "red"
message_colours = [str(colors.rgb2hex(colour_map(i))) for i in range(r.results.messages)]

def msg_label(num):
    if hasattr(r.results, "fake_messages"):
        if num > r.results.normal_messages:
            return "FMsg"
        else:
            return "Msg"
    else:
        return "Msg"

#------------------------------------------------------------
# set up figure and animation
fig = plt.gcf() 

pos = nx.get_node_attributes(r.graph, 'pos')

def init():
    global attacker_responded_to
    attacker_responded_to = []

def animate(i):
    global attacker_responded_to
    fig.clf()

    ax = fig.gca()
    #ax.axis("equal")
    
    attacker_at_node = r.attacker_positions[i]

    # When the attacker is on a node set it to red
    colours = ["w"] * len(r.results.coords)
    colours[attacker_at_node-1] = attacker_colour

    # Draw circles behind nodes when broadcasting
    for (nid, msg) in r.broadcasts_at_time[i]:
        c = plt.Circle(r.results.coords[nid-1], radius=0.25, color=message_colours[msg-1], label=msg)
        ax.add_patch(c)

        if i > 0 and r.attacker_positions[i] != r.attacker_positions[i-1] and attacker_at_node == nid:
            attacker_responded_to.append(msg)

    # Draw the graph
    nx.draw(r.graph, pos, node_size=750, node_color=colours)

    labels = nx.draw_networkx_labels(r.graph, pos, nx.get_node_attributes(r.graph, 'label'), font_size=16)

    anno_str = "Time Step {}, actual time is {:.3f} seconds\n".format(i, i/r.results.slots_per_second) + \
               "Responded to {} messages".format(attacker_responded_to)
    ax.annotate(anno_str, (0.1,-0.4)) # add text

    legend_patches = [
        mpatches.Patch(color=colour, label=msg_label(msg) + ' {}'.format(msg))
        for (colour, msg)
        in zip(message_colours, range(1, r.results.messages+1))
    ]
    lgd = ax.legend(handles=legend_patches, loc=(-0.15,0.2))

ani = animation.FuncAnimation(fig, animate, frames=r.time_steps,
                              interval=2500, blit=False, init_func=init,
                              repeat=True, repeat_delay=2500)


# save the animation as an mp4.  This requires ffmpeg or mencoder to be
# installed.  The extra_args ensure that the x264 codec is used, so that
# the video can be embedded in html5.  You may need to adjust this for
# your system: for more information, see
# http://matplotlib.sourceforge.net/api/animation_api.html
ani.save('{}.mp4'.format(results_name), extra_args=['-vcodec', 'libx264'])
ani.save('{}.gif'.format(results_name), writer='imagemagick')

plt.show()
