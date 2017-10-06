from __future__ import print_function, division

import ast
from collections import OrderedDict, defaultdict
import importlib
import re

from attrdict import AttrDict

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
    il_array = re.sub(r"([0-9]+)\s+(?=[0-9]+)", r"\1,", il_array)
    il_array = il_array.replace("]\n", "],\n")
    il_array = il_array.replace("{", "[")
    il_array = il_array.replace("}", "]")

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
    def __init__(self, results, objective, name):
        #self.results = results
        self.objective = objective
        self.name = name

        self.final = False

        for (k, v) in results.items():
            setattr(self, k, v)

        self.coords = ilp_array_tuple_eval(results.coords)

        self.neighbours_to = ilp_array_neighbour_dicts(results.neighbours_to)
        self.neighbours_from = ilp_array_neighbour_dicts(results.neighbours_from)

        self.nodes = list(range(1, len(self.coords)+1))

        self.graph = nx.DiGraph()
        self.graph.add_nodes_from(self.nodes)

        # Store the coordinates
        for (nid, coord) in enumerate(self.coords, start=1):
            self.graph.node[nid]['pos'] = coord
            self.graph.node[nid]['label'] = nid

            self.graph.node[nid]['color'] = 'w'
            self.graph.node[nid]['shape'] = 'o'
            self.graph.node[nid]['size'] = 350

        for nid in self.sources:
            self.graph.node[nid]['shape'] = 'p'
            self.graph.node[nid]['size'] = 550

        for sink_id in self.sinks:
            self.graph.node[sink_id]['shape'] = 'H'
            self.graph.node[sink_id]['size'] = 550

        # Add edges
        for (nid, nid_neighbours) in self.neighbours_to.items():
            self.graph.add_edges_from((n, nid) for n in nid_neighbours)

        for (nid, nid_neighbours) in self.neighbours_from.items():
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

    @staticmethod
    def parse_file(file_name):
        meta_data_re = re.compile(r"<<< ([a-z ]+), at ([0-9.e+-]+)s, took ([0-9.e+-]+)s")
        other_data_re = re.compile(r"([a-zA-Z ]+): (.+)")
        solution_re = re.compile(r"// solution ([0-9]+) with objective (.+)")
        main_return_re = re.compile(r"main returns ([0-9]+)")

        time_info = OrderedDict()
        info = {}
        objectives = {}
        solution_number = None
        profiles = defaultdict(list)
        main_return = None

        read_profile = False

        lines = defaultdict(list)

        with open(file_name, "r") as input_file:
            for line in input_file:

                match = meta_data_re.match(line)
                if match is not None:
                    time_info[match.group(1)] = (float(match.group(2)), float(match.group(3)))

                    if match.group(1) == "profile":
                        read_profile = False

                    continue

                match = other_data_re.match(line)
                if match is not None:
                    info[match.group(1)] = match.group(2)
                    continue

                match = solution_re.match(line)
                if match is not None:
                    solution_number = int(match.group(1))
                    objectives[solution_number] = float(match.group(2))
                    continue

                match = main_return_re.match(line)
                if match is not None:
                    main_return = int(match.group(1))
                    if main_return != 0:
                        print("Main returned error code {}".format(main_return))
                    continue

                if line.startswith('Profiler Report'):
                    read_profile = True
                    continue

                if read_profile:
                    profiles[solution_number].append(line)
                    continue

                if solution_number is not None:
                    lines[solution_number].append(line)

        results = []

        for (solno, solno_lines) in lines.items():

            gvar, lvar = AttrDict(), AttrDict()

            exec("".join(solno_lines), gvar, lvar)

            if len(lvar) == 0:
                raise IncompleteResultFileError(results_name)

            #print(time_info)
            #print(info)

            result = Results(lvar, objective=objectives[solno], name=file_name)

            results.append(result)

        # Check that we got a final result
        if main_return is not None:
            results[-1].final = True

        return results



    def get_cmap(self):
        '''Returns a function that maps each index in 0, 1, ... N-1 to a distinct 
        RGBA color.'''
        N = self.messages
        color_norm  = colors.Normalize(vmin=0, vmax=N)
        scalar_map = cmx.ScalarMappable(norm=color_norm, cmap='hsv') 
        def map_index_to_rgb_color(index):
            return scalar_map.to_rgba(index)
        return map_index_to_rgb_color

    def message_colours(self):
        colour_map = self.get_cmap()
        return [str(colors.rgb2hex(colour_map(i))) for i in range(self.messages)]

    def msg_label(self, num):
        if hasattr(self, "fake_messages") and num > self.normal_messages:
            return "FMsg"
        else:
            return "Msg"

    def verify(self):
        """Check if the results are sound"""

        # For each broadcast, check that the attacker made a move
        for (time, broadcasts) in enumerate(self.broadcasts_at_time):
            attacker_move = self.attacker_moves_at_time[time]

            print(time, broadcasts, attacker_move)
