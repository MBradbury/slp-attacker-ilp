#!/usr/bin/env python
from __future__ import print_function, division

import argparse
import os
import sys

import matplotlib.pyplot as plt
import networkx as nx

from results.parser import Results

class ILPAttackerDrawer(object):
    def __init__(self, results_name, with_node_id=False):
        self.results_name = results_name
        self.with_node_id = with_node_id

        self.r = Results(results_name)

        self.shortest_path_lengths = {src: nx.shortest_path_length(self.r.graph, source=src) for src in self.r.results.sources}

        moves = []

        for (time, pair) in enumerate(self.r.attacker_moves_at_time):
            if time == 0:
                xvalue = pair[0] if with_node_id else self.min_src_distance(pair[0])

                moves.append((xvalue, time))

            if pair[0] != pair[1]:
                xvalue = pair[1] if with_node_id else self.min_src_distance(pair[1])

                moves.append((xvalue, time))

        print(moves)

        self.moves = moves

    def min_src_distance(self, nid):
        return min(dist[nid] for dist in self.shortest_path_lengths.values())

    def draw(self, show=True):
        fig = plt.figure()
        ax = fig.gca()

        x, t = zip(*self.moves)

        ax.plot(x, t, label="attacker path")
        ax.scatter(x, t, c='b', marker='o')
        ax.legend()

        if self.with_node_id:
            ax.set_xlabel("Node ID")
            ax.set_xticks(self.r.results.neighbours.keys())
        else:
            ax.set_xlabel("Minimum Source Distance (hops)")
            ax.set_xlim(left=0)

        ax.set_ylabel("Time (seconds)")
        ax.set_ylim(bottom=0)

        if not os.path.exists('out'):
            os.makedirs('out')

        plt.savefig('out/{}_attacker2d.pdf'.format(self.results_name.replace(".", "_")))

        if show:
            plt.show()


parser = argparse.ArgumentParser(description="ILP Draw Attacker 2D", add_help=True)
parser.add_argument("--results", metavar="R", nargs="+")
parser.add_argument("--no-show", action='store_true', default=False)
parser.add_argument("--with-node-id", action='store_true', default=False)

args = parser.parse_args(sys.argv[1:])

for result in args.results:
    result = result.replace("/", ".")
    if result.endswith(".py"):
        result = result[:-3]

    print("Creating graph for ", result)

    drawer = ILPAttackerDrawer(result, with_node_id=args.with_node_id)

    drawer.draw(show=not args.no_show)
