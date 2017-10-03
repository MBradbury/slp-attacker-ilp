#!/usr/bin/env python3
import argparse
from collections import defaultdict, namedtuple, OrderedDict
import itertools
import math
import multiprocessing
import os
import subprocess
import sys

import networkx as nx
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from results.parser import Results, IncompleteResultFileError

TimeNid = namedtuple("TimeNid", ("time", "nid"))

def trim_whitespace(file):
    if file.endswith('.pdf'):
        subprocess.check_call(["pdfcrop", file, file])
    elif file.endswith('.png'):
        subprocess.check_call(["convert", file, "-trim", file])
    else:
        raise RuntimeError("Unknown file type")

class ILPMessageDrawer(object):
    def __init__(self, results, iteration, output_format):
        self.r = results
        self.iteration = iteration
        self.output_format = output_format

        real_moves = defaultdict(list)

        for (time, nid_and_msgs) in enumerate(self.r.broadcasts_at_time):
            for (nid, msg) in nid_and_msgs:
                real_moves[msg].append(TimeNid(time, nid))

        self.real_moves = dict(real_moves)

        self.message_colours = self.r.message_colours()

    def draw_all(self):
        out_dir = os.path.join("out", self.r.name.replace(".", "_"), self.iteration)

        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        num_messages = self.r.messages

        for msg in range(1, num_messages+1):

            plt.clf()

            fig, ax = plt.subplots()

            ax.set_aspect("equal")
            ax.set_axis_off()
            ax.invert_yaxis()
            #ax.set_title("Message {}".format(msg))

            self.draw_subplot(msg, ax)

            file = os.path.join(out_dir, '{}.{}'.format(msg, self.output_format))
            fig.savefig(file)
            trim_whitespace(file)

    def draw_all_together(self, show=True):

        num_messages = self.r.messages
        x = int(math.floor(math.sqrt(num_messages)))
        y = int(math.ceil(num_messages / x))

        #print(x, y, num_messages)

        fig, axs = plt.subplots(x, y, figsize=(18.0, 12.0))

        for (msg, ax) in zip(range(1, num_messages+1), axs.reshape(-1)):
            ax.set_aspect("equal")
            ax.set_title("Message {}".format(msg))
            ax.set_axis_off()
            ax.invert_yaxis()
            self.draw_subplot(msg, ax)

        for ax in itertools.islice(axs.reshape(-1), num_messages, None):
            ax.axis("off")

        if not os.path.exists('out'):
            os.makedirs('out')

        file = 'out/{}_msg_{}.{}'.format(self.r.name.replace(".", "_"), self.iteration, self.output_format)
        fig.savefig(file)
        trim_whitespace(file)

        if show:
            plt.show()

    def draw_subplot(self, msg, ax):
        real_moves_to_show = self.real_moves.get(msg, tuple())

        message_colours = self.r.message_colours()

        graph = nx.DiGraph(self.r.graph)

        # Set up message edges
        graph.remove_edges_from(graph.edges())

        edges = OrderedDict()

        for (time_slot, nid) in sorted(real_moves_to_show, key=lambda x: x[0]):
            for neigh in self.r.graph.neighbors(nid):
                if (neigh, nid) in edges:
                    continue

                if (nid, neigh) not in edges:
                    edges[(nid, neigh)] = set()

                edges[(nid, neigh)].add(time_slot)

        for k in edges.keys():
            edges[k] = str(list(sorted(edges[k])))[1:-1]

        graph.add_edges_from((x, y) for (x, y) in edges.keys())

        node_shapes = {node_data['shape'] for (node, node_data) in graph.nodes(data=True)}
        
        pos = nx.get_node_attributes(graph, 'pos')
        col = nx.get_node_attributes(graph, 'color')
        sizes = nx.get_node_attributes(graph, 'size')

        for shape in node_shapes:
            nodes = [node for (node, node_data) in graph.nodes(data=True) if node_data['shape'] == shape]

            color = [col[nid] for nid in nodes]
            size = [sizes[nid] for nid in nodes]

            drawn_nodes = nx.draw_networkx_nodes(graph, pos,
                node_shape=shape,
                node_color=color,
                node_size=size,
                nodelist=nodes,
                ax=ax,
            )

            drawn_nodes.set_edgecolor('black')

        nx.draw_networkx_edges(graph, pos,
            edge_color=self.message_colours[msg-1],
            width=3.5,
            arrows=True,
            ax=ax,
        )

        nx.draw_networkx_edge_labels(graph, pos,
            edge_labels=edges,
            ax=ax,
        )

        nx.draw_networkx_labels(graph, pos,
            labels=nx.get_node_attributes(graph, 'label'),
            font_size=12,
            ax=ax,
        )

def draw(result, i, args):
    drawer = ILPMessageDrawer(result, i, output_format=args.format)

    if args.combine:
        drawer.draw_all_together(show=not args.no_show)
    else:
        drawer.draw_all()

    plt.clf()
