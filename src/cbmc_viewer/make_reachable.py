#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# -*- mode: python-mode -*-

"""List reachable functions in a goto binary."""

import argparse
import sys

from cbmc_viewer import optionst
from cbmc_viewer import reachablet

################################################################

def create_parser():
    """Command line parser."""

    parser = argparse.ArgumentParser(
        description='List reachable functions in a goto binary.'
    )

    optionst.viewer_reachable(parser)
    optionst.goto(parser)
    optionst.srcdir(parser)

    parser.add_argument(
        'cbmc_reachable',
        nargs='*',
        help="""
        A list of xml or json files containing the output of
        'goto-analyzer --show-reachable'.  Do not mix xml and json files.
        """
    )

    optionst.log(parser)

    return parser

################################################################

def main():
    """List reachable functions in a goto binary."""

    args = create_parser().parse_args()
    args = optionst.defaults(args)

    try:
        reachable = reachablet.make_reachable(args)
        print(reachable)
    except UserWarning as error:
        sys.exit(error)

if __name__ == "__main__":
    main()
