#!/usr/bin/env python
from __future__ import print_function, division

import argparse
import os
import subprocess
import sys

import matplotlib
import matplotlib.pyplot as plt
import networkx as nx

from draw.common import trim_whitespace
from results.parser import Results, IncompleteResultFileError

font = {"size": "18"}

class ILPAttackerDrawer(object):
    def __init__(self, results, iteration, output_format, with_node_id=False):
        self.results = results
        self.iteration = iteration
        self.output_format = output_format
        self.with_node_id = with_node_id

        self.shortest_path_lengths = {src: nx.shortest_path_length(self.results.graph, source=src) for src in self.results.sources}

        moves = []

        for (time, pair) in enumerate(self.results.attacker_moves_at_time):

            bcasts = [msg for (nid, msg) in self.results.broadcasts_at_time[time] if nid == pair[1]]

            if time == 0:
                xvalue = pair[0] if with_node_id else self.min_src_distance(pair[0])

                moves.append((xvalue, time, None, pair[0]))

            elif pair[0] != pair[1]:
                xvalue = pair[1] if with_node_id else self.min_src_distance(pair[1])

                moves.append((xvalue, time, bcasts[0], pair[1]))

        print(moves)

        self.moves = moves

    def min_src_distance(self, nid):
        return min(dist[nid] for dist in self.shortest_path_lengths.values())

    def draw(self, show=True):
        fig = plt.figure()
        ax = fig.gca()

        xs, ts, labels, targets = zip(*self.moves)

        ax.plot(xs, ts, label="attacker path")
        ax.scatter(xs, ts, c='b', marker='o')
        #ax.legend()

        for ((x1, t1, label1, tar1), (x2, t2, label2, tar2)) in zip(self.moves, self.moves[1:]):
            x = (x1 + x2) / 2
            y = (t1 + t2) / 2

            ax.annotate(label2,
                xy=(x, y),
                bbox={"boxstyle": "round,pad=0.25", "fc": "white"},
                va="center",
                ha="center",
                backgroundcolor="white",
                **font
            )

        if self.with_node_id:
            ax.set_xlabel("Node ID", **font)
            ax.set_xticks(self.results.nodes)
        else:
            for (x, t, label, target) in self.moves:
                ax.annotate(target,
                    xy=(x, t),
                    xytext=(0, 17.5),
                    textcoords="offset points",
                    va="center",
                    ha='center',
                    **font
                )

            ax.set_xlabel("Minimum Source Distance (hops)", **font)
            ax.set_xlim(left=0)

        ax.set_ylabel("Time (slots)", **font)
        ax.set_ylim(bottom=0)

        ax.tick_params(axis='both', which='major', labelsize=16)
        ax.tick_params(axis='both', which='minor', labelsize=16)

        if not os.path.exists('out'):
            os.makedirs('out')

        file = 'out/{}_attacker2d_{}.{}'.format(self.results.name.replace(".", "_"), self.iteration, self.output_format)
        fig.savefig(file)
        trim_whitespace(file)

        if show:
            plt.show()

def draw(result, i, args):
    drawer = ILPAttackerDrawer(result, i, output_format=args.format, with_node_id=args.with_node_id)
    drawer.draw(show=not args.no_show)

    plt.clf()
