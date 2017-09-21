from __future__ import print_function, division

import ast
import importlib
import re

import matplotlib.colors as colors
import matplotlib.cm as cmx

import networkx as nx

def ilp_ndarray_str_eval(il_array):
    il_array = il_array.strip()
    il_array = il_array.replace("\n", " ")
    il_array = il_array.replace("0 ", "0, ")
    il_array = il_array.replace("1 ", "1, ")
    il_array = il_array.replace("]", "],")

    return ast.literal_eval(il_array[:-1])

def ilp_array_tuple_set_eval(il_array):
    il_array = il_array.strip()
    il_array = il_array.replace("\n", "")
    il_array = il_array.replace("        ", "")
    il_array = il_array.replace(" {", ",{")
    il_array = il_array.replace("{<", "(")
    il_array = il_array.replace(">}", ")")
    il_array = il_array.replace(" ", ",")

    return ast.literal_eval(il_array)

def ilp_array_dicts_eval(il_array):
    il_array = il_array.strip()
    il_array = il_array.replace(" {", ",{")
    il_array = il_array.replace("\n", ",")
    il_array = il_array.replace("         ", "")
    il_array = il_array.replace("{", "[")
    il_array = il_array.replace("}", "]")
    il_array = il_array.replace(" ", ",")

    return ast.literal_eval(il_array)

def ilp_array_msgs_eval(il_array):
    il_array = il_array.strip()
    il_array = il_array.replace("\n", ",")
    il_array = il_array.replace("         ", "")
    il_array = il_array.replace(" ", ",")

    return ast.literal_eval(il_array)

def ilp_array_tuple_eval(il_array):
    il_array = il_array.strip()

    il_array = re.sub(r"<([0-9]+) ([0-9]+)>", r"(\1, \2),", il_array)

    return ast.literal_eval(il_array)

def ilp_array_neighbour_dicts(il_array):

    il_array = il_array.strip()
    il_array = il_array.replace("\n", "")
    il_array = il_array.replace("    ", "")
    il_array = il_array.replace(" ", ", ")

    # Python 2.7 doesn't support set literals for literal_eval
    # Covert to a list here, then convert to a set later
    il_array = il_array.replace("{", "[")
    il_array = il_array.replace("}", "]")

    arr = ast.literal_eval(il_array)

    return {k: set(v) for (k, v) in enumerate(arr, start=1)}

class Results(object):
    def __init__(self, results_name):
        self.results_name = results_name.replace("/", ".")
        if self.results_name.endswith(".py"):
            self.results_name = self.results_name[:-3]

        results = importlib.import_module(self.results_name)
        self.results = results

        if hasattr(self.results, "source_ids"):
            self.results.sources = self.results.source_ids

        if hasattr(self.results, "sink_id"):
            self.results.sink_ids = {self.results.sink_id}

        if isinstance(self.results.coords, str):
            self.results.coords = ilp_array_tuple_eval(self.results.coords)

        if hasattr(self.results, "neighbours"):
            if isinstance(self.results.neighbours, str):
                self.results.neighbours = ilp_array_neighbour_dicts(self.results.neighbours)
        else:
            self.results.neighbours_to = ilp_array_neighbour_dicts(self.results.neighbours_to)
            self.results.neighbours_from = ilp_array_neighbour_dicts(self.results.neighbours_from)

        self.graph = nx.DiGraph()
        self.graph.add_nodes_from(range(1, len(results.coords)+1))

        # Store the coordinates
        for (nid, coord) in enumerate(results.coords, start=1):
            self.graph.node[nid]['pos'] = coord
            self.graph.node[nid]['label'] = nid

            self.graph.node[nid]['color'] = 'w'
            self.graph.node[nid]['shape'] = 'o'
            self.graph.node[nid]['size'] = 350

        for nid in results.sources:
            self.graph.node[nid]['shape'] = 'p'
            self.graph.node[nid]['size'] = 550

        if hasattr(self.results, "sink_ids"):
            for sink_id in self.results.sink_ids:
                self.graph.node[sink_id]['shape'] = 'H'
                self.graph.node[sink_id]['size'] = 550

        # Add edges
        if hasattr(self.results, "neighbours"):
            for (nid, nid_neighbours) in self.results.neighbours.items():
                self.graph.add_edges_from((nid, n) for n in nid_neighbours)
                self.graph.add_edges_from((n, nid) for n in nid_neighbours)
        else:
            for (nid, nid_neighbours) in self.results.neighbours_to.items():
                self.graph.add_edges_from((n, nid) for n in nid_neighbours)

            for (nid, nid_neighbours) in self.results.neighbours_from.items():
                self.graph.add_edges_from((nid, n) for n in nid_neighbours)


        if hasattr(results, "attacker_path"):
            attacker_path = ilp_ndarray_str_eval(results.attacker_path)

            self.attacker_moves_at_time = [results.attacker_edges[moves.index(1)] for moves in attacker_path]
        else:
            self.attacker_moves_at_time = ilp_array_tuple_set_eval(results.used_edges)


        self.broadcasts_at_time = [set() for _ in self.attacker_moves_at_time]

        if hasattr(results, "broadcasts"):
            broadcasts = ilp_ndarray_str_eval(results.broadcasts)

            for (nid, mess_and_time) in enumerate(broadcasts, start=1):
                for (mess, times) in enumerate(mess_and_time, start=1):
                    try:
                        time = times.index(1)

                        self.broadcasts_at_time[time].add((nid, mess))
                    except ValueError:
                        pass
        elif hasattr(results, "broadcasted_at"):
            broadcasts_by_nodes_at_time = ilp_array_dicts_eval(results.broadcasted_at)

            for (nid, bcasts_by_nid_at_time) in enumerate(broadcasts_by_nodes_at_time, start=1):
                for (mess, times) in enumerate(bcasts_by_nid_at_time, start=1):
                    for time in times:
                        self.broadcasts_at_time[time].add((nid, mess))

        elif hasattr(results, "broadcasted_msg_at"):
            broadcasts_by_nodes_at_time = ilp_array_msgs_eval(results.broadcasted_msg_at)

            for (nid, bcasts_by_nid_at_time) in enumerate(broadcasts_by_nodes_at_time, start=1):
                for (time, mess) in enumerate(bcasts_by_nid_at_time, start=0):
                    if mess != 0:
                        self.broadcasts_at_time[time].add((nid, mess))
        else:
            raise RuntimeError("Unknown broadcasted field")


        self.attacker_positions = [v for (u, v) in self.attacker_moves_at_time]

        self.time_steps = len(self.attacker_moves_at_time)

        #self.verify()

    def get_cmap(self):
        '''Returns a function that maps each index in 0, 1, ... N-1 to a distinct 
        RGBA color.'''
        N = self.results.messages
        color_norm  = colors.Normalize(vmin=0, vmax=N)
        scalar_map = cmx.ScalarMappable(norm=color_norm, cmap='hsv') 
        def map_index_to_rgb_color(index):
            return scalar_map.to_rgba(index)
        return map_index_to_rgb_color

    def message_colours(self):
        colour_map = self.get_cmap()
        return [str(colors.rgb2hex(colour_map(i))) for i in range(self.results.messages)]

    def msg_label(self, num):
        if hasattr(self.results, "fake_messages"):
            if num > self.results.normal_messages:
                return "FMsg"
            else:
                return "Msg"
        else:
            return "Msg"


    def verify(self):
        """Check if the results are sound"""

        # For each broadcast, check that the attacker made a move
        for (time, broadcasts) in enumerate(self.broadcasts_at_time):
            attacker_move = self.attacker_moves_at_time[time]

            print(time, broadcasts, attacker_move)

