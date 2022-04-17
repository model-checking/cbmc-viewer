# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Report the results of cbmc.

Report the results of cbmc with annotated source files indiciating
line coverage, with coverage reports for statically reachable functions,
and with lists of property violations and traces for each violation.
"""

from pathlib import Path
import argparse
import datetime
import logging
import os
import sys

from cbmc_viewer import configt
from cbmc_viewer import coveraget
from cbmc_viewer import loopt
from cbmc_viewer import optionst
from cbmc_viewer import propertyt
from cbmc_viewer import reachablet
from cbmc_viewer import report
from cbmc_viewer import resultt
from cbmc_viewer import sourcet
from cbmc_viewer import symbolt
from cbmc_viewer import tracet

def create_parser():
    """Create the command line parser."""

    parser = argparse.ArgumentParser(
        description='Report CBMC results.'
    )

    cbmc_data = parser.add_argument_group(
        """CBMC results""",
        """CBMC results from property checking, coverage checking, and
        property listing.  Specify at least one of property checking
        or coverage checking, using either "CBMC results" here or
        "Viewer data" below."""
    )
    optionst.result(cbmc_data)
    optionst.coverage(cbmc_data)
    optionst.property(cbmc_data)

    proof_sources = parser.add_argument_group('Sources')
    optionst.srcdir(proof_sources)
    optionst.exclude(proof_sources)
    optionst.extensions(proof_sources)
    optionst.source_method(proof_sources)

    proof_binaries = parser.add_argument_group('Binaries')
    optionst.wkdir(proof_binaries)
    optionst.goto(proof_binaries)

    viewer_output = parser.add_argument_group('Output')
    optionst.reportdir(viewer_output)
    viewer_output.add_argument(
        '--json-summary',
        metavar='JSON',
        help='Write summary of key metrics to this json file.'
    )

    viewer_data = parser.add_argument_group(
        """Viewer data""",
        """JSON files produced by the various make-* scripts."""
    )
    optionst.viewer_coverage(viewer_data)
    optionst.viewer_loop(viewer_data)
    optionst.viewer_property(viewer_data)
    optionst.viewer_reachable(viewer_data)
    optionst.viewer_result(viewer_data)
    optionst.viewer_source(viewer_data)
    optionst.viewer_symbol(viewer_data)
    optionst.viewer_trace(viewer_data)

    other = parser.add_argument_group('Other')
    optionst.log(other)
    optionst.config(other)
    optionst.version(other)

    deprecated = parser.add_argument_group(
        'Depricated',
        'Options from prior versions now deprecated.'
    )
    deprecated = optionst.block(deprecated)
    deprecated = optionst.htmldir(deprecated)
    deprecated = optionst.srcexclude(deprecated)
    deprecated = optionst.blddir(deprecated)
    deprecated = optionst.storm(deprecated)

    return parser

################################################################

class Timer:
    """A simple timer for display in progress information."""

    def __init__(self):
        self.time = datetime.datetime.now()

    def reset(self):
        """Reset timer to current time."""

        self.time = datetime.datetime.now()

    def elapsed(self):
        """Reset timer and return time elapsed since last reset."""

        old = self.time
        self.time = datetime.datetime.now()
        return (self.time - old).total_seconds()

TIMER = Timer()

def progress(msg, done=False):
    """Display local progress for a single step."""

    if done:
        time = TIMER.elapsed()
        logging.info("viewer: %s...done (%s sec)", msg, time)
    else:
        TIMER.reset()
        logging.info("viewer: %s...", msg)

GLOBAL_TIMER = Timer()

def global_progress(msg, done=False):
    """Display overall progress for all steps."""

    if done:
        time = GLOBAL_TIMER.elapsed()
        logging.info("viewer: %s...done (%s sec)", msg, time)
    else:
        GLOBAL_TIMER.reset()
        logging.info("viewer: %s...", msg)

################################################################

def viewer(args):
    """Construct the cbmc report."""

    if not (args.result or args.viewer_result or args.coverage or args.viewer_coverage):
        logging.error("Need property checking results or coverage checking results.")
        sys.exit(1)

    global_progress("CBMC viewer")

    htmldir = os.path.join(args.reportdir, "html")
    jsondir = os.path.join(args.reportdir, "json")
    os.makedirs(htmldir, exist_ok=True)
    os.makedirs(jsondir, exist_ok=True)
    jsondir = Path(jsondir)

    progress("Scanning property checking results")
    results = resultt.make_and_save_result(args, jsondir / 'viewer-result.json')
    progress("Scanning property checking results", True)

    progress("Scanning error traces")
    traces = tracet.make_and_save_trace(args, jsondir / 'viewer-trace.json')
    progress("Scanning error traces", True)

    progress("Scanning coverage data")
    coverage = coveraget.make_and_save_coverage(args, jsondir / 'viewer-coverage.json')
    progress("Scanning coverage data", True)

    progress("Scanning loop definitions")
    loops = loopt.make_and_save_loop(args, jsondir / 'viewer-loop.json')
    progress("Scanning loop definitions", True)

    progress("Scanning properties")
    properties = propertyt.make_and_save_property(args, jsondir / 'viewer-property.json')
    progress("Scanning properties", True)

    progress("Computing reachable functions")
    reachablet.make_and_save_reachable(args, jsondir / 'viewer-reachable.json')
    progress("Computing reachable functions", True)

    # Make sources last, it may delete the goto binary
    progress("Scanning source tree")
    sources = sourcet.make_and_save_source(args, jsondir / 'viewer-source.json')
    progress("Scanning source tree", True)

    progress("Preparing symbol table")
    symbols = symbolt.make_and_save_symbol(args, jsondir / 'viewer-symbol.json')
    progress("Preparing symbol table", True)

    config = configt.Config(args.config)
    report.report(config, sources, symbols, results, coverage, traces,
                  properties, loops, htmldir, progress)

    global_progress("CBMC viewer", True)
    return 0 # exit with normal return code

################################################################

def main():
    """Construct the cbmc report."""

    args = create_parser().parse_args()
    args = optionst.defaults(args)
    viewer(args)
