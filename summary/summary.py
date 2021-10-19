#!/usr/bin/env python3

import csv
import argparse
import logging
import sys
import subprocess
import os
import json

import stubs

################################################################

def create_parser():
    desc = "Summarize stubs and undefined functions in proof repositories."
    args = [
        {
            "flag": "--github",
            "default": "projects.json",
            "help": "JSON file defining proof projects and repositories "
                    "(default: %(default)s)"
        },
        {
            "flag": "--project",
            "nargs": "*",
            "default": [],
            "help": "Names of proof projects to summarize "
                    "(default: all projects)"
        },
        {
            "flag": "--clean",
            "action": "store_true",
            "help": "Remove proof results and proof summaries"
        },
        {
            "flag": "--clone",
            "action": "store_true",
            "help": "Clone proof project"
        },
        {
            "flag": "--build",
            "action": "store_true",
            "help": "Build proof project (run proofs)"
        },
        {
            "flag": "--summarize",
            "action": "store_true",
            "help": "Summarize project proof results"
        },
        {
            "flag": "--chart",
            "action": "store_true",
            "help": "Write project summary data as JSON to stdout"
        },
        {
            "flag": "--verbose",
            "action": "store_true",
            "help": "Verbose output"
        },
        {
            "flag": "--debug",
            "action": "store_true",
            "help": "Debug output"
        }
    ]
    epilog = None

    parser = argparse.ArgumentParser(description=desc, epilog=epilog)
    for arg in args:
        flag = arg['flag']
        del arg['flag']
        parser.add_argument(flag, **arg)
    return parser

def parse_arguments():
    return create_parser().parse_args()

def configure_logger(verbose=False, debug=False):
    # Logging is configured by the first invocation of logging.basicConfig
    fmt = '%(levelname)s: %(message)s'
    if debug:
        logging.basicConfig(level=logging.DEBUG, format=fmt)
    if verbose:
        logging.basicConfig(level=logging.INFO, format=fmt)
    logging.basicConfig(format=fmt)

################################################################
# Shell out commands

def run(cmd, cwd=None, encoding=None):
    """Run a command in a subshell and return the standard output."""

    kwds = {
        'cwd': cwd,
    }
    if sys.version_info >= (3, 6): # encoding introduced in Python 3.6
        kwds['encoding'] = encoding

    logging.debug("Running %s", ' '.join(cmd))
    result = subprocess.run(cmd, **kwds, check=False)
    if result.returncode:
        logging.debug('Failed command: %s', ' '.join(cmd))
        result.check_returncode()

################################################################
#

def clean_project(project_path):
    if not os.path.isdir(project_path):
        logging.info('%s does not exist: not cleaning %s',
                     project_path, project_path)
        return

    logging.info('Cleaning %s', project_path)
    run(['git', 'clean', '-fdx'], cwd=project_path)
    run(['git', 'checkout', '.'], cwd=project_path)

def clone_project(project_url):
    project_path = os.path.basename(project_url)

    if os.path.isdir(project_path):
        logging.info('%s exists: not cloning %s into %s',
                     project_path, project_url, project_path)
        return project_path

    logging.info('Cloning %s into %s', project_url, project_path)
    run(['git', 'clone', project_url])
    run(['git', 'submodule', 'update', '--init', '--checkout', '--recursive'],
        cwd=project_path)

    return project_path

def build_project(project_path, proofs_path):

    if not os.path.isdir(project_path):
        logging.info('%s does not exist: not running proofs in project %s',
                     project_path, project_path)
        return

    path = os.path.join(project_path, proofs_path)

    logging.info('Running %s proofs in %s', project_path, path)
    run(['./run-cbmc-proofs.py'], cwd=path)

def summarize_project(project_path, proofs_path):
    if not os.path.isdir(project_path):
        logging.info('%s does not exist: not summarizing project %s',
                     project_path, project_path)
        return None

    path = os.path.join(project_path, proofs_path)

    # Simulate invocation of summary script until args removed from script API
    args = stubs.parse_arguments(
        ['--srcdir', project_path, '--proofdir', path]
    )
    args = stubs.compute_default_arguments(args)

    summary = stubs.scan_proofs(args.proof, args)
    stubbed = stubs.defined_histogram(summary, 'stubbed')
    removed = stubs.undefined_histogram(summary, 'removed')
    missing = stubs.undefined_histogram(summary, 'missing')

    return {
        'stubbed': stubbed,
        'removed': removed,
        'missing': missing
    }

################################################################
#

def chart_projects_csv(summary):
    # pylint: disable = line-too-long
    writer = csv.writer(sys.stdout)
    writer.writerow([''] + list(summary))
    writer.writerow([])
    writer.writerow(['stubbed'] + [len(summary[project]['stubbed']['count'] or []) for project in summary])
    writer.writerow(['removed'] + [len(summary[project]['removed']['count'] or []) for project in summary])
    writer.writerow(['missing'] + [len(summary[project]['missing']['count'] or []) for project in summary])
    writer.writerow([])
    writer.writerow(['stubbed audited'] + [0 for project in summary])
    writer.writerow(['removed audited'] + [0 for project in summary])
    writer.writerow(['missing audited'] + [0 for project in summary])
    writer.writerow([])
    writer.writerow(['stubbed issues'] + [0 for project in summary])
    writer.writerow(['removed issues'] + [0 for project in summary])
    writer.writerow(['missing issues'] + [0 for project in summary])
    writer.writerow([])
    writer.writerow(['stubbed unaudited'] + [len(summary[project]['stubbed']['count'] or []) for project in summary])
    writer.writerow(['removed unaudited'] + [len(summary[project]['removed']['count'] or []) for project in summary])
    writer.writerow(['missing unaudited'] + [len(summary[project]['missing']['count'] or []) for project in summary])

def chart_projects_json(summary):
    result = {}

    for project in summary:
        data = summary[project]
        result[project] = {
            "stubbed": sorted(data['stubbed']['count']),
            "removed": sorted(data['removed']['count']),
            "missing": sorted(data['missing']['count']),
            "stubbed-audited": [],
            "removed-audited": [],
            "missing-audited": [],
            "stubbed-issues": [],
            "removed-issues": [],
            "missing-issues": [],
            "stubbed-resolved": [],
            "removed-resolved": [],
            "missing-resolved": [],
        }
    return json.dumps(result, indent=2)

################################################################
#

def main():
    args = parse_arguments()
    args.project = [os.path.normpath(project) for project in args.project]

    configure_logger(args.verbose, args.debug)

    with open(args.github, encoding="utf-8") as handle:
        github = json.load(handle)

    summary = {}

    if not args.project:
        args.project = list(github)

    for project in args.project:
        project_repo = github[project]['github']
        proofs_path = github[project]['proofs']
        project_path = os.path.basename(project_repo)
        if args.clean:
            clean_project(project_path)
        if args.clone:
            clone_project(project_repo)
        if args.build:
            build_project(project_path, proofs_path)
        if args.summarize or args.chart:
            result = summarize_project(project_path, proofs_path)
            if result:
                summary[project] = result

    if args.summarize:
        print(json.dumps(summary, indent=2))

    if args.chart:
        print(chart_projects_json(summary))

if __name__ == "__main__":
    main()
