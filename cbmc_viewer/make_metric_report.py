#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# -*- mode: python-mode -*-

"""Generate CBMC runtime analysis metrics report."""


import argparse
import sys

from cbmc_viewer import metric_reportt
from cbmc_viewer import optionst

def create_parser():
    """Command line parser."""

    parser = argparse.ArgumentParser(
        description="Generate CBMC runtime analysis metrics report."
    )

    optionst.proof(parser)
    optionst.srcdir(parser)
    optionst.reportdir(parser)

    optionst.log(parser)

    return parser

################################################################

def main():
    """Generate CBMC runtime analysis metrics report."""

    args = create_parser().parse_args()
    args = optionst.defaults(args)

    try:
        runtime_analysis = \
            metric_reportt.RuntimeAnalysisSummary(args.proof,
                                                  args.srcdir)
        runtime_analysis.dump(outdir=args.reportdir)
    except UserWarning as error:
        sys.exit(error)

if __name__ == "__main__":
    main()
