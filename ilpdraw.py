#!/usr/bin/env python3

import argparse
import multiprocessing
import sys

from draw import animator, attacker2d, attacker3d, messages
from results.parser import Results, IncompleteResultFileError

actions = {
    "attacker2d": attacker2d,
    "attacker3d": attacker3d,
    "animator": animator,
    "messages": messages,
}

class Runner(object):
    def __init__(self, args):
        self.args = args
        self.action_fn = actions[args.action].draw

    def run(self, result_name):
        print("Creating graph for ", result_name)

        try:
            results_data = Results.parse_file(result_name)
        except IncompleteResultFileError as ex:
            print(ex, file=sys.stderr)
            return

        to_iterate = list(enumerate(results_data))

        # Mark the final result as final
        # but only if it exists
        try:
            if to_iterate[-1][1].final:
                to_iterate[-1] = ("final", to_iterate[-1][1])
        except IndexError:
            print("No results", file=sys.stderr)
            return

        if not self.args.intermediate:
            to_iterate = [to_iterate[-1]]

        for (i, result_data) in to_iterate:
            self.action_fn(result_data, i, self.args)

def _add_common(subparser):
    subparser.add_argument("results", metavar="R", nargs="+")
    subparser.add_argument("--thread-count", type=int, default=None)
    subparser.add_argument("--no-show", action='store_true', default=False)
    subparser.add_argument("--intermediate", action='store_true', default=False)

def main():
    parser = argparse.ArgumentParser(description="ILP Draw", add_help=True)
    subparsers = parser.add_subparsers(title="action", dest="action")

    subparser = subparsers.add_parser("attacker2d")
    _add_common(subparser)
    subparser.add_argument("--format", choices=["pdf", "png"], default="pdf")
    subparser.add_argument("--with-node-id", action='store_true', default=False)

    subparser = subparsers.add_parser("attacker3d")
    _add_common(subparser)
    subparser.add_argument("--format", choices=["pdf", "png"], default="pdf")

    subparser = subparsers.add_parser("animator")
    _add_common(subparser)
    subparser.add_argument("--format", required=True, choices=["gif", "mp4", "frames", "none"])

    subparser = subparsers.add_parser("messages")
    _add_common(subparser)
    subparser.add_argument("--format", choices=["pdf", "png"], default="pdf")
    subparser.add_argument("--combine", action='store_true', default=False)
    
    args = parser.parse_args(sys.argv[1:])

    runner = Runner(args)

    # Limit max tasks per child to avoid matplotlib using too much RAM
    pool = multiprocessing.Pool(args.thread_count, maxtasksperchild=3)

    pool.map(runner.run, args.results)

if __name__ == "__main__":
    main()
