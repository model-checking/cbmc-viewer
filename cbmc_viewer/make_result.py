#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# -*- mode: python-mode -*-

"""List CBMC property checking results."""

import argparse
import sys

from cbmc_viewer import optionst
from cbmc_viewer import resultt

def create_parser():
    """Command line parser."""

    parser = argparse.ArgumentParser(
        description='List CBMC property checking results.'
    )

    optionst.viewer_result(parser)
    parser.add_argument(
        'cbmc_result',
        nargs='*',
        help="""
        One or more files containing the output of cbmc property checking
        as text, xml, or json.
        Multiple files will be merged into a single list of
        property checking results.
        Do not mix text, xml, and json files.
        """
    )

    optionst.log(parser)

    return parser

################################################################

def main():
    """List CBMC property checking results."""

    args = create_parser().parse_args()
    args = optionst.defaults(args)

    try:
        results = resultt.make_result(args.viewer_result, args.cbmc_result)
        print(results)
    except UserWarning as error:
        sys.exit(error)

if __name__ == "__main__":
    main()
