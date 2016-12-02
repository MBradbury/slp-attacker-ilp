#!/usr/bin/env python
from __future__ import print_function, division

import argparse
import sys

import matplotlib.pyplot as plt
import networkx as nx

from results.parser import Results

results_name = sys.argv[1]

parser = argparse.ArgumentParser(description="ILP Draw Attacker 2D", add_help=True)
parser.add_argument("results")
parser.add_argument("--with-node-id", action='store_true', default=False)

args = parser.parse_args(sys.argv[1:])

r = Results(args.results)

sources = {1}

moves = []

if not args.with_node_id:
    shortest_path_lengths = {src: nx.shortest_path_length(r.graph, source=src) for src in sources}

    def min_src_distance(nid):
        return min(dist[nid] for dist in shortest_path_lengths.values())

for (time, pair) in enumerate(r.attacker_moves_at_time):
    if time == 0:
        xvalue = pair[0] if args.with_node_id else min_src_distance(pair[0])

        moves.append((xvalue, time))

    if pair[0] != pair[1]:
        xvalue = pair[1] if args.with_node_id else min_src_distance(pair[1])

        moves.append((xvalue, time))

print(moves)

fig = plt.figure()
ax = fig.gca()

x, t = zip(*moves)

ax.plot(x, t, label="attacker path")
ax.scatter(x, t, c='b', marker='o')
ax.legend()

if args.with_node_id:
    ax.set_xlabel("Node ID")
    ax.set_xticks(r.results.neighbours.keys())
else:
    ax.set_xlabel("Minimum Source Distance (hops)")
    ax.set_xlim(left=0)

ax.set_ylabel("Time (seconds)")
ax.set_ylim(bottom=0)


#plt.savefig('this.png')

plt.show()
