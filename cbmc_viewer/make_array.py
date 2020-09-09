#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# -*- mode: python-mode -*-

"""List CBMC array constraint metrics."""


import argparse
import sys

from cbmc_viewer import arrayt
from cbmc_viewer import optionst

def create_parser():
    """Command line parser."""

    parser = argparse.ArgumentParser(
        description="List CBMC array constraint metrics."
    )

    optionst.array(parser)
    optionst.reportdir(parser)

    optionst.log(parser)

    return parser

################################################################

def main():
    """List CBMC array constraint metrics."""

    args = create_parser().parse_args()
    args = optionst.defaults(args)

    try:
        array = arrayt.ArrayConstraintSummary(args.array)
        array.dump(outdir=args.reportdir)
    except UserWarning as error:
        sys.exit(error)

if __name__ == "__main__":
    main()
