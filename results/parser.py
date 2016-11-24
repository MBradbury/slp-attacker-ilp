from __future__ import print_function, division

import ast
import importlib

import networkx as nx

def ilp_ndarray_str_eval(il_array):
    il_array = il_array.strip()
    il_array = il_array.replace("\n", " ")
    il_array = il_array.replace("0 ", "0, ")
    il_array = il_array.replace("1 ", "1, ")
    il_array = il_array.replace("]", "],")

    return ast.literal_eval(il_array[:-1])

def ilp_array_tuple_eval(il_array):
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
    il_array = il_array.replace("         ", " ")
    il_array = il_array.replace("{", "[")
    il_array = il_array.replace("}", "]")

    return ast.literal_eval(il_array)

def ilp_array_msgs_eval(il_array):
    il_array = il_array.strip()
    il_array = il_array.replace("\n", ",")
    il_array = il_array.replace("         ", "")
    il_array = il_array.replace(" ", ",")

    return ast.literal_eval(il_array)

class Results(object):
    def __init__(self, results_name):
        self.results_name = results_name

        results = importlib.import_module(results_name)
        self.results = results

        self.graph = nx.Graph()
        self.graph.add_nodes_from(range(1, len(results.coords)+1))

        # Store the coordinates
        for (nid, coord) in enumerate(results.coords, start=1):
            self.graph.node[nid]['pos'] = coord
            self.graph.node[nid]['label'] = nid

        # Add edges
        for (nid, nid_neighbours) in results.neighbours.items():
            self.graph.add_edges_from((nid, n) for n in nid_neighbours)


        if hasattr(results, "attacker_path"):
            attacker_path = ilp_ndarray_str_eval(results.attacker_path)

            self.attacker_moves_at_time = [results.attacker_edges[moves.index(1)] for moves in attacker_path]
        else:
            self.attacker_moves_at_time = ilp_array_tuple_eval(results.used_edges)


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
                    if len(times) == 1:
                        self.broadcasts_at_time[times[0]].add((nid, mess))
                    elif len(times) == 0:
                        pass
                    else:
                        raise RuntimeError("Invalid time size of {}".format(len(times)))

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
