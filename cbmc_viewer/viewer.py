# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Report the results of cbmc.

Report the results of cbmc with annotated source files indiciating
line coverage, with coverage reports for statically reachable functions,
and with lists of property violations and traces for each violation.
"""

import argparse
import datetime
import json
import logging
import os

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

# runtime analysis metrics
from cbmc_viewer import arrayt

def create_parser():
    """Create the command line parser."""

    parser = argparse.ArgumentParser(
        description='Report CBMC results.'
    )

    cbmc_data = parser.add_argument_group(
        """CBMC data""",
        """Output of 'cbmc' for property checking, coverage checking, etc."""
    )
    optionst.result(cbmc_data)
    optionst.coverage(cbmc_data)
    optionst.property(cbmc_data)

    # runtime analysis metrics
    optionst.array(cbmc_data)

    proof_sources = parser.add_argument_group('Sources')
    optionst.srcdir(proof_sources)
    optionst.exclude(proof_sources)
    optionst.extensions(proof_sources)
    optionst.source_method(proof_sources)
    optionst.tags_method(proof_sources)

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

    depricated = parser.add_argument_group(
        'Depricated',
        'Options from prior versions now depricated.'
    )
    depricated = optionst.block(depricated)
    depricated = optionst.htmldir(depricated)
    depricated = optionst.srcexclude(depricated)
    depricated = optionst.blddir(depricated)
    depricated = optionst.storm(depricated)

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

def viewer():
    """Construct the cbmc report."""

    args = create_parser().parse_args()
    args = optionst.defaults(args)

    global_progress("CBMC viewer")

    htmldir = os.path.join(args.reportdir, "html")
    jsondir = os.path.join(args.reportdir, "json")
    os.makedirs(htmldir, exist_ok=True)
    os.makedirs(jsondir, exist_ok=True)

    def dump(obj, name):
        with open(os.path.join(jsondir, name), 'w') as output:
            output.write(str(obj))

    progress("Scanning property checking results")
    results = resultt.do_make_result(args.viewer_result, args.result)
    dump(results, 'viewer-result.json')
    progress("Scanning property checking results", True)

    progress("Scanning error traces")
    traces = tracet.do_make_trace(args.viewer_trace, args.result,
                                  args.srcdir, args.wkdir)
    dump(traces, 'viewer-trace.json')
    progress("Scanning error traces", True)

    progress("Scanning coverage data")
    coverage = coveraget.do_make_coverage(args.viewer_coverage,
                                          args.srcdir,
                                          args.coverage)
    dump(coverage, 'viewer-coverage.json')
    progress("Scanning coverage data", True)

    progress("Scanning loop definitions")
    loops = loopt.do_make_loop(args.viewer_loop, None,
                               args.srcdir, args.goto)
    dump(loops, 'viewer-loop.json')
    progress("Scanning loop definitions", True)

    progress("Scanning properties")
    properties = propertyt.do_make_property(args.viewer_property,
                                            args.property,
                                            args.srcdir)
    dump(properties, 'viewer-property.json')
    progress("Scanning properties", True)

    progress("Computing reachable functions")
    reachable = reachablet.do_make_reachable(args.viewer_reachable,
                                             None,
                                             args.srcdir,
                                             args.goto)
    dump(reachable, 'viewer-reachable.json')
    progress("Computing reachable functions", True)

    # Make sources last, it may delete the goto binary
    progress("Scanning source tree")
    sources = sourcet.do_make_source(args.viewer_source,
                                     args.goto,
                                     args.source_method,
                                     args.srcdir, args.wkdir,
                                     args.exclude, args.extensions)
    dump(sources, 'viewer-source.json')
    progress("Scanning source tree", True)

    progress("Preparing symbol table")
    symbols = symbolt.do_make_symbol(args.viewer_symbol, args.viewer_source,
                                     args.tags_method,
                                     args.goto, args.wkdir,
                                     args.srcdir, None)
    dump(symbols, 'viewer-symbol.json')
    progress("Preparing symbol table", True)

    if args.array:
        progress("Scanning array constraint data")
        array = arrayt.do_make_array(args.array)
        dump(array, 'viewer-array.json')
        progress("Scanning array constraint data", True)
    else:
        array = None

    config = configt.Config(args.config)
    report.report(config, sources, symbols, results, coverage, traces,
                  properties, loops, array, htmldir, progress)

    global_progress("CBMC viewer", True)
