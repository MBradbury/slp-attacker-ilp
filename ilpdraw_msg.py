#!/usr/bin/env python
from __future__ import print_function, division

from collections import defaultdict, namedtuple, OrderedDict
import math
import os
import sys

import networkx as nx
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from results.parser import Results

TimeNid = namedtuple("TimeNid", ("time", "nid"))

class ILPMessageDrawer(object):
    def __init__(self, results_name):
        self.results_name = results_name

        self.r = Results(results_name)

        real_moves = defaultdict(list)

        for (time, nid_and_msgs) in enumerate(self.r.broadcasts_at_time):
            for (nid, msg) in nid_and_msgs:
                real_moves[msg].append(TimeNid(time, nid))

        self.real_moves = dict(real_moves)

        print(self.real_moves)

        self.message_colours = self.r.message_colours()

    def draw_all(self):

        num_messages = self.r.results.messages
        x = math.floor(math.sqrt(num_messages))
        y = math.ceil(num_messages / x)

        print(x, y, num_messages)

        plt.figure(figsize=(20.0, 12.0))

        for msg in range(1, num_messages+1):

            ax = plt.subplot(x, y, msg)
            ax.set_aspect("equal")
            ax.set_title("Message {}".format(msg))
            self.draw_subplot(msg)

        plt.tight_layout()

        if not os.path.exists('out'):
            os.makedirs('out')

        plt.savefig('out/{}_msg.pdf'.format(self.results_name))

        plt.show()

    def draw_subplot(self, msg):
        real_moves_to_show = self.real_moves.get(msg, tuple())

        message_colours = self.r.message_colours()

        graph = nx.DiGraph(self.r.graph)

        # Set up message edges
        graph.remove_edges_from(graph.edges())

        edges = OrderedDict()

        for (time_slot, nid) in real_moves_to_show:
            for neigh in self.r.graph.neighbors(nid):
                if (neigh, nid) not in edges:
                    edges[(nid, neigh)] = time_slot

        graph.add_edges_from((x, y) for (x, y) in edges.keys())

        print(graph.edges())

        pos = nx.get_node_attributes(graph, 'pos')

        nx.draw(graph, pos,
                node_color=["w"] * len(pos),
                labels=nx.get_node_attributes(graph, 'label'),
                edge_color=self.message_colours[msg-1], width=3.5, arrows=True)
        nx.draw_networkx_edge_labels(graph, pos=pos, edge_labels=edges)

results_name = sys.argv[1]

drawer = ILPMessageDrawer(results_name)

drawer.draw_all()
