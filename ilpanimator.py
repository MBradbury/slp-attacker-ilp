#!/usr/bin/env python
from __future__ import print_function, division

import argparse
import os
import sys

import networkx as nx
import numpy as np

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from results.parser import Results

class ILPAnimator(object):
    def __init__(self, results_name):
        self.attacker_responded_to = []

        self.r = Results(results_name)

        self.attacker_colour = "red"
        self.message_colours = self.r.message_colours()

        self.width = (1 + 1 + max(x for (x,y) in self.r.results.coords)) * 2
        self.height = (1 + max(y for (x,y) in self.r.results.coords)) * 2

        self.fig = plt.figure(figsize=(self.width, self.height))
        self.fig.subplots_adjust(left=0.1, bottom=0.1, right=1, top=1, wspace=None, hspace=None)

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
        lgd = ax.legend(handles=legend_patches, loc=(-0.075, 0.5))


parser = argparse.ArgumentParser(description="ILP Animator", add_help=True)
parser.add_argument("results", metavar="R", nargs="+")
parser.add_argument("--format", required=True, choices=["gif", "mp4", "none"])
parser.add_argument("--no-show", action='store_true', default=False)

args = parser.parse_args(sys.argv[1:])

if not os.path.exists('out'):
        os.makedirs('out')

for result in args.results:
    result = result.replace("/", ".")
    if result.endswith(".py"):
        result = result[:-3]

    print("Animating {}".format(result))

    anim = ILPAnimator(result)

    ani = animation.FuncAnimation(anim.fig, anim.animate, frames=anim.r.time_steps,
                                  interval=2500, blit=False, init_func=anim.init,
                                  repeat=True, repeat_delay=2500)

    path = None

    if args.format == "mp4":
        # save the animation as an mp4.  This requires ffmpeg or mencoder to be
        # installed.  The extra_args ensure that the x264 codec is used, so that
        # the video can be embedded in html5.  You may need to adjust this for
        # your system: for more information, see
        # http://matplotlib.sourceforge.net/api/animation_api.html
        path = 'out/{}_anim.mp4'.format(result.replace(".", "_"))
        ani.save(path, extra_args=['-vcodec', 'libx264'])

    elif args.format == "gif":
        path = 'out/{}_anim.gif'.format(result.replace(".", "_"))
        ani.save(path, writer='imagemagick')

    elif args.format == "none":
        pass

    else:
        raise RuntimeError("Unknown format {}".format(args.format))

    if path is not None:
        print("Saved as {}".format(path))

    if not args.no_show:
        plt.show()
