#!/usr/bin/env python
from __future__ import print_function, division

import os
import sys

import networkx as nx
import numpy as np

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from results.parser import Results

results_name = sys.argv[1]

class ILPAnimator(object):
    def __init__(self, results_name):
        self.attacker_responded_to = []

        self.r = Results(results_name)

        self.attacker_colour = "red"
        self.message_colours = self.r.message_colours()

        self.width = (2 + 1 + max(x for (x,y) in self.r.results.coords)) * 2.25
        self.height = (1 + max(y for (x,y) in self.r.results.coords)) * 2.25

        self.fig = plt.figure(figsize=(self.width, self.height))

    def init(self):
        self.attacker_responded_to = []

    def animate(self, step):
        r = self.r
        fig = self.fig

        fig.clf()

        ax = fig.gca()
        ax.axis("equal")
        
        attacker_at_node = r.attacker_positions[step]

        # When the attacker is on a node set it to red
        colours = ["w"] * len(r.results.coords)
        colours[attacker_at_node-1] = self.attacker_colour

        # Draw circles behind nodes when broadcasting
        for (nid, msg) in r.broadcasts_at_time[step]:
            c = mpatches.Circle(r.results.coords[nid-1], radius=0.25, color=self.message_colours[msg-1], label=msg)
            ax.add_patch(c)

            if step > 0 and r.attacker_positions[step] != r.attacker_positions[step-1] and attacker_at_node == nid:
                self.attacker_responded_to.append(msg)

        pos = nx.get_node_attributes(self.r.graph, 'pos')

        # Draw the graph
        nx.draw(r.graph, pos,
                node_size=750, node_color=colours,
                labels=nx.get_node_attributes(r.graph, 'label'), font_size=16)

        anno_str = "Time Step {}, actual time is {:.3f} seconds\n".format(step, step/r.results.slots_per_second) + \
                   "Responded to {} messages".format(self.attacker_responded_to)
        ax.annotate(anno_str, (0,-0.5)) # add text

        legend_patches = [
            mpatches.Patch(color=colour, label=r.msg_label(msg) + ' {}'.format(msg))
            for (colour, msg)
            in zip(self.message_colours, range(1, r.results.messages+1))
        ]
        lgd = ax.legend(handles=legend_patches, loc=(0, 0.5))

anim = ILPAnimator(results_name)

ani = animation.FuncAnimation(anim.fig, anim.animate, frames=anim.r.time_steps,
                              interval=2500, blit=False, init_func=anim.init,
                              repeat=True, repeat_delay=2500)

if not os.path.exists('out'):
    os.makedirs('out')

# save the animation as an mp4.  This requires ffmpeg or mencoder to be
# installed.  The extra_args ensure that the x264 codec is used, so that
# the video can be embedded in html5.  You may need to adjust this for
# your system: for more information, see
# http://matplotlib.sourceforge.net/api/animation_api.html
ani.save('out/{}_anim.mp4'.format(results_name), extra_args=['-vcodec', 'libx264'])
#ani.save('out/{}_anim.gif'.format(results_name), writer='imagemagick')

plt.show()
