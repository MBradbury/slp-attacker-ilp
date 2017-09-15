#!/usr/bin/env python

import argparse
import itertools
import subprocess
import sys

dats = ["3x3", "4x4", "5x5"]

"""source_ids = ["{1}", "{1}", "{1}"]
sink_ids = ["{9}", "{16}", "{13}"]

attacker_start_poses = [9, 16, 13]
attacker_range = [1.0]

source_periods = [1]
safety_periods = [5, 7, 9]
slots_per_second = [6, 7, 9]"""

all_options = {
    "obj": [0, 1, 2, 3, 4],
    "num_fake_messages": [0, 3],
    "message_sent_once": [0, 1],
}

option_keys = ("obj", "num_fake_messages", "message_sent_once")

def estimate_walltime(dat, options):
    if dat == "3x3":
        return "01:00:00"
    elif dat == "4x4":
        return "16:00:00"
    elif dat == "5x5":
        return "48:00:00"
    else:
        return "60:00:00"


class Cluster(object):
    def __init__(self, dry_run):
        self.dry_run = dry_run

    def job_name(self, dat, options):
        return dat + "_" + "_".join(map(str, options))

    def pbs_submit(self, command, job_name, walltime, notify=None, *args, **kwargs):
        submit_command = "msub -j oe -h -l nodes={}:ppn={} -l walltime={} -l mem={} -N \"{}\" -q {}".format(
            self.nodes, self.ppn, walltime, self.pmem, job_name, self.queue
        )

        if notify:
            submit_command += " -m bae -M {}".format(notify)

        cluster_command = "echo '{} >> ilp{}.py' | {}".format(command, job_name, submit_command)

        self._submit_job(cluster_command)

    def _submit_job(self, command):
        print(command)
        if not self.dry_run:
            subprocess.check_call(command, shell=True)

class Tinis(Cluster):
    nodes = 1
    ppn = 32
    pmem = "32220mb"
    queue = "fat"

    def __init__(self, dry_run):
        super(Tinis, self).__init__(dry_run)

    def generate_command(self, dat, options):
        options_string = " ".join("-D {}={}".format(k, v) for (k, v) in options.items())

        return "oplrun -v -w -deploy {} -p SLP {}".format(options_string, dat)

    def submit_command(self, *args, **kwargs):
        return self.pbs_submit(*args, **kwargs)

    def submit_all(self, notify):
        option_product = list(itertools.product(*[all_options[key] for key in option_keys]))

        for dat in dats:
            for options in option_product:
                options_dict = dict(zip(option_keys, options))

                walltime = estimate_walltime(dat, options_dict)

                command = self.generate_command(dat, options_dict)
                job_name = self.job_name(dat, options)

                self.submit_command(command, job_name, notify=notify, walltime=walltime)

def cluster_names():
    return [cluster.__name__ for cluster in Cluster.__subclasses__()]

def get_cluster(name):
    return [cluster for cluster in Cluster.__subclasses__() if cluster.__name__ == name][0]

def main():
    parser = argparse.ArgumentParser(description="Cluster Submitter", add_help=True)

    parser.add_argument("cluster", type=str, help="The name of the cluster", choices=cluster_names())
    parser.add_argument("--notify", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true", default=False)

    args = parser.parse_args(sys.argv[1:])

    cluster = get_cluster(args.cluster)(args.dry_run)

    cluster.submit_all(notify=args.notify)

if __name__ == "__main__":
    main()
