#!/usr/bin/env python
from __future__ import print_function, division

import argparse
import os
import sys

import networkx as nx
import numpy as np

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from results.parser import Results

parser = argparse.ArgumentParser(description="ILP Draw Attacker 3D", add_help=True)
parser.add_argument("results")

args = parser.parse_args(sys.argv[1:])

r = Results(args.results)

moves = []

for (time, pair) in enumerate(r.attacker_moves_at_time):
	if time == 0:
		(x, y) = r.results.coords[pair[0]-1]

		moves.append((x, y, time))

	if pair[0] != pair[1]:
		(x, y) = r.results.coords[pair[1]-1]

		moves.append((x, y, time))

print(moves)

fig = plt.figure()
ax = fig.gca(projection='3d')

x, y, t = zip(*moves)

ax.plot(x, y, t, label="attacker path")
ax.scatter(x, y, t, c='b', marker='o')
ax.legend()

ax.set_zlabel("time")

pos = nx.get_node_attributes(r.graph, 'pos')
nx.draw_networkx_nodes(r.graph, ax=ax, pos=pos)
#nx.draw_networkx_labels(r.graph, ax=ax, pos=pos)

#nx.draw_networkx_edges(dg, pos=pos, edgelist=real_moves.keys(), edge_color="red", arrows=True)
#nx.draw_networkx_edge_labels(dg, pos=pos, edge_labels=real_moves)

if not os.path.exists('out'):
    os.makedirs('out')

plt.savefig('out/{}_attacker3d.pdf'.format(args.results))

plt.show()
