#!/usr/bin/env python
from __future__ import print_function, division

import sys

import matplotlib.pyplot as plt

from results.parser import Results

results_name = sys.argv[1]

r = Results(results_name)

moves = []

for (time, pair) in enumerate(r.attacker_moves_at_time):
	if time == 0:
		moves.append((pair[0], time))

	if pair[0] != pair[1]:
		moves.append((pair[1], time))

print(moves)

fig = plt.figure()
ax = fig.gca()

x, t = zip(*moves)

ax.plot(x, t, label="attacker path")
ax.scatter(x, t, c='b', marker='o')
ax.legend()

ax.set_xlabel("Node ID")
ax.set_ylabel("time")

ax.set_ylim(bottom=0)
ax.set_xticks(r.results.neighbours.keys())

#plt.savefig('this.png')

plt.show()
