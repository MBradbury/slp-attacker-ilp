#!/usr/bin/env python
from __future__ import print_function, division

import argparse
from collections import defaultdict, namedtuple, OrderedDict
import math
import os
import subprocess
import sys

import networkx as nx
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from results.parser import Results

TimeNid = namedtuple("TimeNid", ("time", "nid"))

def trim_whitespace(file):
    if file.endswith('.pdf'):
        subprocess.check_call(["pdfcrop", file, file])
    elif file.endswith('.png'):
        subprocess.check_call(["convert", file, "-trim", file])
    else:
        raise RuntimeError("Unknown file type")

class ILPMessageDrawer(object):
    def __init__(self, results_name, output_format):
        self.results_name = results_name
        self.output_format = output_format

        self.r = Results(results_name)

        real_moves = defaultdict(list)

        for (time, nid_and_msgs) in enumerate(self.r.broadcasts_at_time):
            for (nid, msg) in nid_and_msgs:
                real_moves[msg].append(TimeNid(time, nid))

        self.real_moves = dict(real_moves)

        print(self.real_moves)

        self.message_colours = self.r.message_colours()

    def draw_all(self):
        out_dir = os.path.join("out", self.results_name.replace(".", "_"))

        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        num_messages = self.r.results.messages

        for msg in range(1, num_messages+1):

            plt.clf()

            ax = plt.gca()

            ax.set_aspect("equal")
            ax.set_axis_off()
            ax.invert_yaxis()
            #ax.set_title("Message {}".format(msg))

            self.draw_subplot(msg)

            file = os.path.join(out_dir, '{}.{}'.format(msg, self.output_format))
            plt.savefig(file)
            trim_whitespace(file)

    def draw_all_together(self, show=True):

        num_messages = self.r.results.messages
        x = math.floor(math.sqrt(num_messages))
        y = math.ceil(num_messages / x)

        print(x, y, num_messages)

        plt.figure(figsize=(18.0, 12.0))

        for msg in range(1, num_messages+1):

            ax = plt.subplot(x, y, msg)
            ax.set_aspect("equal")
            ax.set_title("Message {}".format(msg))
            ax.set_axis_off()
            ax.invert_yaxis()
            self.draw_subplot(msg)

        if not os.path.exists('out'):
            os.makedirs('out')

        file = 'out/{}_msg.{}'.format(self.results_name.replace(".", "_"), self.output_format)
        plt.savefig(file)
        trim_whitespace(file)

        if show:
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
            )

            drawn_nodes.set_edgecolor('black')

        nx.draw_networkx_edges(graph, pos,
            edge_color=self.message_colours[msg-1],
            width=3.5,
            arrows=True
        )

        nx.draw_networkx_edge_labels(graph, pos,
            edge_labels=edges
        )

        nx.draw_networkx_labels(graph, pos,
            labels=nx.get_node_attributes(graph, 'label'),
            font_size=12
        )

parser = argparse.ArgumentParser(description="ILP Draw Messages", add_help=True)
parser.add_argument("results", metavar="R", nargs="+")
parser.add_argument("--no-show", action='store_true', default=False)
parser.add_argument("--combine", action='store_true', default=False)
parser.add_argument("--format", choices=["pdf", "png"], default="pdf")

args = parser.parse_args(sys.argv[1:])

for result in args.results:
    print("Creating graph for ", result)

    drawer = ILPMessageDrawer(result, output_format=args.format)

    if args.combine:
        drawer.draw_all_together(show=not args.no_show)
    else:
        drawer.draw_all()
