#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# -*- mode: python-mode -*-

"""List CBMC error traces."""

import argparse
import sys

from cbmc_viewer import optionst
from cbmc_viewer import tracet

def create_parser():
    """Command line parser."""

    parser = argparse.ArgumentParser(
        description="List CBMC error traces."
    )

    optionst.viewer_trace(parser)
    optionst.wkdir(parser)
    optionst.srcdir(parser)

    parser.add_argument(
        'cbmc_trace',
        nargs='*',
        help="""
        An xml or json file containing the output of cbmc property checking.
        Merge the traces if more than one file is given.
        Do not mix xml and json files.
        """
    )

    optionst.log(parser)

    return parser

################################################################

def main():
    """List CBMC error traces."""

    args = create_parser().parse_args()
    args = optionst.defaults(args)

    try:
        traces = tracet.make_trace(args.viewer_trace, args.cbmc_trace, args.srcdir, args.wkdir)
        print(traces)
    except UserWarning as error:
        sys.exit(error)

if __name__ == "__main__":
    main()
