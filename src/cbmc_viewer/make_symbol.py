#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# -*- mode: python-mode -*-

"""List the symbols used to build a goto binary."""

import argparse
import sys

from cbmc_viewer import optionst
from cbmc_viewer import symbolt

################################################################

def create_parser():
    """Command line parser."""

    parser = argparse.ArgumentParser(
        description="List the symbols used to build a goto binary."
    )

    optionst.viewer_symbol(parser)
    optionst.viewer_source(parser)

    optionst.goto(parser)
    optionst.wkdir(parser)
    optionst.srcdir(parser)

    parser.add_argument(
        '--files',
        nargs='+',
        metavar='FILE',
        help="""
        A list of FILES to scan for symbols.
        The files may be specified as either absolute paths or paths
        relative to root.
        """
    )

    optionst.log(parser)

    return parser

################################################################

def main():
    """List the symbols used to build a goto binary."""

    args = create_parser().parse_args()
    args = optionst.defaults(args)

    try:
        symbolt.make_and_save_symbol(args)
    except UserWarning as error:
        sys.exit(error)

if __name__ == "__main__":
    main()
