# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Assemble the full report for cbmc viewer."""

import logging
import os
import shutil

import pkg_resources

from cbmc_viewer import markup_code
from cbmc_viewer import markup_summary
from cbmc_viewer import markup_trace

PACKAGE = 'cbmc_viewer'
VIEWER_JS = 'viewer.js'
VIEWER_CSS = 'viewer.css'

def progress_default(string):
    """A default method for logging progress."""

    logging.info(string)

def report(config, sources, symbols, results, coverage, traces, properties,
           loops, array, report_dir='.', progress=progress_default):
    """Assemble the full report for cbmc viewer."""

    # The report is assembled from many sources of data
    # pylint: disable=too-many-locals

    # Some code depends on these definitions
    #   * links to traces in summary produced with jinja summary template
    #   * links to sources in traces produced by markup_trace
    #   * links to css and js in traces produced with jinja trace template
    code_dir = report_dir
    trace_dir = os.path.join(report_dir, markup_trace.TRACES)

    os.makedirs(report_dir, exist_ok=True)
    shutil.copy(pkg_resources.resource_filename(PACKAGE, VIEWER_CSS),
                report_dir)
    shutil.copy(pkg_resources.resource_filename(PACKAGE, VIEWER_JS),
                report_dir)

    progress("Preparing report summary")
    markup_summary.Summary(
        coverage, symbols, results, properties, loops, config).dump(
            outdir=report_dir)
    progress("Preparing report summary", True)

    progress("Annotating source tree")
    for path in sources.files:
        markup_code.Code(sources.root, path, symbols, coverage).dump(
            outdir=code_dir)
    progress("Annotating source tree", True)

    progress("Annotating traces")
    snippets = markup_trace.CodeSnippet(sources.root)
    for name, trace in traces.traces.items():
        markup_trace.Trace(name, trace, symbols, properties, loops, snippets).dump(
            outdir=trace_dir)
    progress("Annotating traces", True)

    progress("Preparing array constraint summary report")
    array.dump(outdir=report_dir)
    progress("Preparing array constraint summary report", True)
