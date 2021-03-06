#!/usr/bin/env python

import argparse
from datetime import timedelta
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
    "obj": [0, 1, 2, 3, 4, 5],
    "num_fake_messages": [0, 3],
    "message_sent_once": [0, 1],
    "target_receive_ratio": [0.6, 0.8, 1.0],
}

option_keys = ("obj", "num_fake_messages", "message_sent_once", "target_receive_ratio")

def estimate_walltime(dat, options):
	return timedelta(hours=48)

    #if dat == "3x3":
    #    return timedelta(hours=6)
    #elif dat == "4x4":
    #    if options["obj"] == 4:
    #        return timedelta(hours=48)
    #    else:
    #        return timedelta(hours=16)
    #elif dat == "5x5":
    #    return timedelta(hours=48)
    #else:
    #    return timedelta(hours=48)


class Cluster(object):
    def __init__(self, dry_run):
        self.dry_run = dry_run

    def job_name(self, dat, options):
        return dat + "_" + "_".join(map(str, options))

    def generate_command(self, dat, options):
        options_string = " ".join("-D {}={}".format(k, v) for (k, v) in options.items())

        return "oplrun -v -w -deploy -profile {} -p SLP {}".format(options_string, dat)

    def _walltime_to_str(self, walltime):
        total_seconds = int(walltime.total_seconds())
        hours, remainder = divmod(total_seconds, 60*60)
        minutes, seconds = divmod(remainder, 60)

        return "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)

    def pbs_submit(self, command, job_name, walltime, notify=None, hold=False, *args, **kwargs):
        submit_command = "qsub -j oe -l nodes={}:ppn={} -l walltime={} -l mem={} -N \"{}\"".format(
            self.nodes, self.ppn, self._walltime_to_str(walltime), self.pmem, job_name
        )

        if hasattr(self, "queue"):
            submit_command += " -q {}".format(self.queue)

        if notify:
            submit_command += " -m bae -M {}".format(notify)

        if hold:
            submit_command += " -h"

        cluster_command = "echo '{} >> ilp{}.txt' | {}".format(command, job_name, submit_command)

        if hasattr(self, "max_walltime"):
            if walltime > self.max_walltime:
                raise RuntimeError("Unable to queue \"{}\" as its walltime is above the maximum".format(cluster_command))

        self._submit_job(cluster_command)

    def moab_submit(self, command, job_name, walltime, notify=None, hold=False, *args, **kwargs):
        submit_command = "msub -j oe -l nodes={}:ppn={} -l walltime={} -l mem={} -N \"{}\"".format(
            self.nodes, self.ppn, self._walltime_to_str(walltime), self.pmem, job_name
        )

        if hasattr(self, "queue"):
            submit_command += " -q {}".format(self.queue)

        if notify:
            submit_command += " -m bae -M {}".format(notify)

        if hold:
            submit_command += " -h"

        cluster_command = "echo '{} >> ilp{}.txt' | {}".format(command, job_name, submit_command)

        if hasattr(self, "max_walltime"):
            if walltime > self.max_walltime:
                raise RuntimeError("Unable to queue \"{}\" as its walltime is above the maximum".format(cluster_command))

        self._submit_job(cluster_command)

    def _submit_job(self, command):
        print(command)
        if not self.dry_run:
            subprocess.check_call(command, shell=True)

    def submit_all(self, **kwargs):
        option_product = list(itertools.product(*[all_options[key] for key in option_keys]))

        for dat in dats:
            for options in option_product:
                try:
                    options_dict = dict(zip(option_keys, options))

                    walltime = estimate_walltime(dat, options_dict)

                    command = self.generate_command(dat, options_dict)
                    job_name = self.job_name(dat, options)

                    self.submit_command(command, job_name, walltime=walltime, **kwargs)
                except RuntimeError as ex:
                    print(ex)

class Tinis(Cluster):
    nodes = 1
    ppn = 32      # Up to 32
    pmem = "512gb" # Up to 1TB
    queue = "fat"
    max_walltime = timedelta(seconds=172800)

    def __init__(self, dry_run):
        super(Tinis, self).__init__(dry_run)

    def submit_command(self, *args, **kwargs):
        return self.moab_submit(*args, **kwargs)

class Orac(Cluster):
    nodes = 1
    ppn = 28      # Up to 28
    pmem = "120gb" # Up to 128GB

    def __init__(self, dry_run):
        super(Orac, self).__init__(dry_run)

    def submit_command(self, *args, **kwargs):
        return self.moab_submit(*args, **kwargs)

class Chiron(Cluster):
    nodes = 1
    ppn = 48      # Up to 96
    pmem = "512gb" # Up to 4TB
    queue = "fat"

    def __init__(self, dry_run):
        super(Chiron, self).__init__(dry_run)

    def submit_command(self, *args, **kwargs):
        return self.pbs_submit(*args, **kwargs)

def cluster_names():
    return [cluster.__name__ for cluster in Cluster.__subclasses__()]

def get_cluster(name):
    return [cluster for cluster in Cluster.__subclasses__() if cluster.__name__ == name][0]

def main():
    parser = argparse.ArgumentParser(description="Cluster Submitter", add_help=True)

    parser.add_argument("cluster", type=str, help="The name of the cluster", choices=cluster_names())
    parser.add_argument("--notify", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument("--hold", action="store_true", default=False)

    args = parser.parse_args(sys.argv[1:])

    cluster = get_cluster(args.cluster)(args.dry_run)

    cluster.submit_all(notify=args.notify, hold=args.hold)

if __name__ == "__main__":
    main()
