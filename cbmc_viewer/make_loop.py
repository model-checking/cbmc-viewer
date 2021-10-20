#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# -*- mode: python-mode -*-

"""List the loops in a goto binary."""

import argparse
import sys

from cbmc_viewer import loopt
from cbmc_viewer import optionst

################################################################

def create_parser():
    """Command line parser."""

    parser = argparse.ArgumentParser(
        description='List loops in a goto binary.'
    )

    optionst.viewer_loop(parser)
    optionst.goto(parser)
    optionst.srcdir(parser)

    parser.add_argument(
        'cbmc_loop',
        nargs='*',
        help="""
        A list of xml or json files containing the output of
        'cbmc --show-loops'.  Do not mix xml and json files.
        """
    )

    optionst.log(parser)

    return parser

################################################################

def main():
    """List the loops in a goto binary."""

    args = create_parser().parse_args()
    args = optionst.defaults(args)

    try:
        loops = loopt.make_loop(args.viewer_loop, args.cbmc_loop, args.srcdir, args.goto)
        print(loops)
    except UserWarning as error:
        sys.exit(error)

if __name__ == "__main__":
    main()
