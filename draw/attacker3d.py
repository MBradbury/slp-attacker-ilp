#!/usr/bin/env python
from __future__ import print_function, division

import argparse
import os
import subprocess
import sys

import networkx as nx
import numpy as np

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from results.parser import Results

class ILPAttackerDrawer(object):
    def __init__(self, results_name):
        self.results_name = results_name

        self.r = Results(results_name)

        moves = []

        for (time, pair) in enumerate(self.r.attacker_moves_at_time):
            if time == 0:
                (x, y) = self.r.results.coords[pair[0]-1]

                moves.append((x, y, time))

            if pair[0] != pair[1]:
                (x, y) = self.r.results.coords[pair[1]-1]

                moves.append((x, y, time))

        print(moves)

        self.moves = moves

    def draw(self, show=True):
        fig = plt.figure()
        ax = fig.gca(projection='3d')

        x, y, t = zip(*self.moves)

        ax.plot(x, y, t, label="attacker path")
        ax.scatter(x, y, t, c='b', marker='o')
        ax.legend()

        ax.set_zlabel("time")

        pos = nx.get_node_attributes(self.r.graph, 'pos')
        nx.draw_networkx_nodes(self.r.graph, ax=ax, pos=pos)
        #nx.draw_networkx_labels(r.graph, ax=ax, pos=pos)

        #nx.draw_networkx_edges(dg, pos=pos, edgelist=real_moves.keys(), edge_color="red", arrows=True)
        #nx.draw_networkx_edge_labels(dg, pos=pos, edge_labels=real_moves)

        if not os.path.exists('out'):
            os.makedirs('out')

        file = 'out/{}_attacker3d.pdf'.format(self.results_name.replace(".", "_"))
        plt.savefig(file)

        subprocess.check_call(["pdfcrop", file, file])

        if show:
            plt.show()

def draw(result, i, args):
    drawer = ILPAttackerDrawer(result)

    drawer.draw(show=not args.no_show)

    plt.clf()
