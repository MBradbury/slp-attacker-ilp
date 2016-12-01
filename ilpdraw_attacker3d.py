#!/usr/bin/env python
from __future__ import print_function, division

from collections import defaultdict
import sys

import networkx as nx
import numpy as np

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from results.parser import Results

results_name = sys.argv[1]

r = Results(results_name)

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

#plt.savefig('this.png')

plt.show()
