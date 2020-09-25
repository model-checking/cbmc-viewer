#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# -*- mode: python-mode -*-

"""List CBMC solver query complexity metrics."""


import argparse
import sys

from cbmc_viewer import clauset
from cbmc_viewer import optionst

def create_parser():
    """Command line parser."""

    parser = argparse.ArgumentParser(
        description="List CBMC solver query complexity metrics."
    )

    optionst.clause(parser)
    optionst.dimacs(parser)
    optionst.core(parser)
    optionst.srcdir(parser)

    optionst.log(parser)

    return parser

################################################################

def main():
    """List CBMC solver query complexity metrics."""

    args = create_parser().parse_args()
    args = optionst.defaults(args)

    try:
        clause = clauset.do_make_clause(args.clause,
                                        args.srcdir,
                                        args.dimacs,
                                        args.core)
        print(clause)
    except UserWarning as error:
        sys.exit(error)

if __name__ == "__main__":
    main()
