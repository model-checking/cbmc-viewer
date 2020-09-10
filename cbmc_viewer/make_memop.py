#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# -*- mode: python-mode -*-

"""List CBMC memory operation call metrics."""


import argparse
import sys

from cbmc_viewer import memopt
from cbmc_viewer import optionst

def create_parser():
    """Command line parser."""

    parser = argparse.ArgumentParser(
        description="List CBMC memory operation call metrics."
    )

    optionst.memop(parser)
    optionst.srcdir(parser)
    optionst.reportdir(parser)

    optionst.log(parser)

    return parser

################################################################

def main():
    """List CBMC memory operation call metrics."""

    args = create_parser().parse_args()
    args = optionst.defaults(args)

    try:
        memop = memopt.MemOpSummary(args.memop,
                                    args.srcdir)
        memop.dump(outdir=args.reportdir)
    except UserWarning as error:
        sys.exit(error)

if __name__ == "__main__":
    main()
