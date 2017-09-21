from __future__ import print_function, division

import ast
from collections import OrderedDict
import importlib
import re

import matplotlib.colors as colors
import matplotlib.cm as cmx

import networkx as nx

class IncompleteResultFileError(RuntimeError):
    def __init__(self, file_path):
        super(IncompleteResultFileError, self).__init__("The results file {} is incomplete.".format(file_path))

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
        self.results_name = results_name

        results = self._parse_file(results_name)
        self.results = results

        if not hasattr(results, "coords"):
            raise IncompleteResultFileError(results_name)

        results.coords = ilp_array_tuple_eval(results.coords)

        results.neighbours_to = ilp_array_neighbour_dicts(results.neighbours_to)
        results.neighbours_from = ilp_array_neighbour_dicts(results.neighbours_from)

        self.nodes = list(range(1, len(results.coords)+1))

        self.graph = nx.DiGraph()
        self.graph.add_nodes_from(self.nodes)

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

        for sink_id in results.sinks:
            self.graph.node[sink_id]['shape'] = 'H'
            self.graph.node[sink_id]['size'] = 550

        # Add edges
        for (nid, nid_neighbours) in results.neighbours_to.items():
            self.graph.add_edges_from((n, nid) for n in nid_neighbours)

        for (nid, nid_neighbours) in results.neighbours_from.items():
            self.graph.add_edges_from((nid, n) for n in nid_neighbours)


        self.attacker_moves_at_time = ilp_array_tuple_set_eval(results.used_edges)

        self.broadcasts_at_time = [set() for _ in self.attacker_moves_at_time]
        for (nid, bcasts_by_nid_at_time) in enumerate(ilp_array_dicts_eval(results.broadcasted_at), start=1):
            for (mess, times) in enumerate(bcasts_by_nid_at_time, start=1):
                for time in times:
                    self.broadcasts_at_time[time].add((nid, mess))

        self.attacker_positions = [v for (u, v) in self.attacker_moves_at_time]

        self.time_steps = len(self.attacker_moves_at_time)

        #self.verify()

    def _parse_file(self, file_name):
        meta_data_re = re.compile(r"<<< ([a-z ]+), at ([0-9.e+-]+)s, took ([0-9.e+-]+)s")
        other_data_re = re.compile(r"([a-zA-Z ]+): (.+)")
        solution_re = re.compile(r"// solution with objective (.+)")

        time_info = OrderedDict()
        info = {}
        objective = None

        lines = []

        with open(file_name, "r") as input_file:
            for line in input_file:

                match = meta_data_re.match(line)
                if match is not None:
                    time_info[match.group(1)] = (float(match.group(2)), float(match.group(3)))
                    continue

                match = other_data_re.match(line)
                if match is not None:
                    info[match.group(1)] = match.group(2)
                    continue

                match = solution_re.match(line)
                if match is not None:
                    objective = float(match.group(1))
                    continue

                if objective is None:
                    lines.append(line)

        gvar, lvar = OrderedDict(), OrderedDict()

        exec("".join(lines), gvar, lvar)

        print(time_info)
        print(info)

        class Result:
            def __init__(self, **kwargs):
                for (k, v) in kwargs.items():
                    setattr(self, k, v)

        return Result(**lvar)



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
