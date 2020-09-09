#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# -*- mode: python-mode -*-

"""List CBMC points-to set metrics."""


import argparse
import sys

from cbmc_viewer import aliast
from cbmc_viewer import optionst

def create_parser():
    """Command line parser."""

    parser = argparse.ArgumentParser(
        description="List CBMC points-to set metrics."
    )

    optionst.alias(parser)
    optionst.reportdir(parser)

    optionst.log(parser)

    return parser

################################################################

def main():
    """List CBMC points-to set metrics."""

    args = create_parser().parse_args()
    args = optionst.defaults(args)

    try:
        alias = aliast.AliasSummary(args.alias)
        alias.dump(outdir=args.reportdir)
    except UserWarning as error:
        sys.exit(error)

if __name__ == "__main__":
    main()
