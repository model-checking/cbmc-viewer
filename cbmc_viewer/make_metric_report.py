#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# -*- mode: python-mode -*-

"""List CBMC runtime analysis metrics."""


import argparse
import sys

from cbmc_viewer import metric_reportt
from cbmc_viewer import optionst

def create_parser():
    """Command line parser."""

    parser = argparse.ArgumentParser(
        description="List CBMC runtime analysis metrics."
    )

    optionst.srcdir(parser)
    optionst.reportdir(parser)

    parser.add_argument(
        '--proof', '-p',
        default=[],
        nargs='+',
        help="""
        Provide list of proofs.
        """,
        required=True)

    optionst.log(parser)

    return parser

################################################################

def main():
    """List CBMC runtime analysis metrics."""

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
