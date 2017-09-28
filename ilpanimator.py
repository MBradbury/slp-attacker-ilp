#!/usr/bin/env python
from __future__ import print_function, division

import argparse
import os
import shutil
import sys

import networkx as nx
import numpy as np

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from results.parser import Results

class FrameWriter(animation.ImageMagickBase, animation.FileMovieWriter):
    '''File-based frame writer.

    Frames are written to temporary files on disk and then stitched
    together at the end.
    '''

    supported_formats = ['png']

    def finish(self):
        # Call run here now that all frame grabbing is done. All temp files
        # are available to be assembled.

        if not os.path.exists(self.outfile):
            os.makedirs(self.outfile)
        else:
            if not os.path.isdir(self.outfile):
                raise RuntimeError("The path {} must be a directory".format(self.outfile))
            else:
                shutil.rmtree(self.outfile)
                os.makedirs(self.outfile)

        for fname in self._temp_names:
            new_name_parts = fname[4:].split(u'.')
            new_name = "{}.{}".format(int(new_name_parts[0]), new_name_parts[1])

            os.rename(fname, os.path.join(self.outfile, new_name))

    def _args(self):
        return None

class ILPAnimator(object):
    def __init__(self, results):
        self.attacker_responded_to = []

        self.results = results

        self.attacker_colour = "red"
        self.message_colours = self.results.message_colours()

        self.width = (1 + 1 + max(x for (x,y) in self.results.coords)) * 2
        self.height = (1 + max(y for (x,y) in self.results.coords)) * 2

        self.fig = plt.figure(figsize=(self.width, self.height))
        self.fig.subplots_adjust(left=0.1, bottom=0.1, right=1, top=1, wspace=None, hspace=None)

    def init(self):
        self.attacker_responded_to = []

    def animate(self, step):
        fig = self.fig

        fig.clf()

        ax = fig.gca()
        ax.axis("equal")
        
        attacker_at_node = self.results.attacker_positions[step]

        # When the attacker is on a node set it to red
        colours = ["w"] * len(self.results.coords)
        colours[attacker_at_node-1] = self.attacker_colour

        # Draw circles behind nodes when broadcasting
        for (nid, msg) in self.results.broadcasts_at_time[step]:
            c = mpatches.Circle(self.results.coords[nid-1], radius=0.25, color=self.message_colours[msg-1], label=msg)
            ax.add_patch(c)

            if step > 0 and self.results.attacker_positions[step] != self.results.attacker_positions[step-1] and attacker_at_node == nid:
                self.attacker_responded_to.append(msg)

        pos = nx.get_node_attributes(self.results.graph, 'pos')

        # Draw the graph
        nx.draw(self.results.graph, pos,
                node_size=750, node_color=colours,
                labels=nx.get_node_attributes(self.results.graph, 'label'), font_size=16)

        anno_str = "Time Step {}, actual time is {:.3f} seconds\n".format(step, step/self.results.slots_per_second) + \
                   "Responded to {} messages".format(self.attacker_responded_to)
        ax.annotate(anno_str, (0,-0.5)) # add text

        legend_patches = [
            mpatches.Patch(color=colour, label=self.results.msg_label(msg) + ' {}'.format(msg))
            for (colour, msg)
            in zip(self.message_colours, range(1, self.results.messages+1))
        ]
        lgd = ax.legend(handles=legend_patches, loc=(-0.075, 0.5))

def draw_one_result(result, i, args):
    anim = ILPAnimator(result)

    ani = animation.FuncAnimation(anim.fig, anim.animate, frames=anim.results.time_steps,
                                  interval=2500, blit=False, init_func=anim.init,
                                  repeat=True, repeat_delay=2500)

    path = None

    if args.format == "mp4":
        # save the animation as an mp4.  This requires ffmpeg or mencoder to be
        # installed.  The extra_args ensure that the x264 codec is used, so that
        # the video can be embedded in html5.  You may need to adjust this for
        # your system: for more information, see
        # http://matplotlib.sourceforge.net/api/animation_api.html
        path = 'out/{}_{}_anim.mp4'.format(result.name.replace(".", "_"), i)
        ani.save(path, writer='ffmpeg', extra_args=['-vcodec', 'libx264'])

    elif args.format == "gif":
        path = 'out/{}_{}_anim.gif'.format(result.name.replace(".", "_"), i)
        ani.save(path, writer='imagemagick')

    elif args.format == "frames":
        path = 'out/{}_{}_frames/'.format(result.name.replace(".", "_"), i)
        ani.save(path, writer=FrameWriter())

        # Can't show these individual frames
        args.no_show = True

    elif args.format == "none":
        pass

    else:
        raise RuntimeError("Unknown format {}".format(args.format))

    if path is not None:
        print("Saved as {}".format(path))

    if not args.no_show:
        plt.show()

    plt.clf()

def main():
    parser = argparse.ArgumentParser(description="ILP Animator", add_help=True)
    parser.add_argument("results", metavar="R", nargs="+")
    parser.add_argument("--format", required=True, choices=["gif", "mp4", "frames", "none"])
    parser.add_argument("--no-show", action='store_true', default=False)
    parser.add_argument("--intermediate", action='store_true', default=False)

    args = parser.parse_args(sys.argv[1:])

    if not os.path.exists('out'):
            os.makedirs('out')

    for result_name in args.results:
        print("Animating {}".format(result_name))

        try:
            results_data = Results.parse_file(result_name)
        except IncompleteResultFileError as ex:
            print(ex)
            continue

        to_iterate = list(enumerate(results_data))
        to_iterate[-1] = ("final", to_iterate[-1][1])

        if not args.intermediate:
            to_iterate = [to_iterate[-1]]

        for (i, result_data) in to_iterate:
            draw_one_result(result_data, i, args)

if __name__ == "__main__":
    main()
