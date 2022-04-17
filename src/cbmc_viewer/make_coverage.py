#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# -*- mode: python-mode -*-

"""List CBMC coverage checking results."""


import argparse
import sys

from cbmc_viewer import coveraget
from cbmc_viewer import optionst

def create_parser():
    """Command line parser."""

    parser = argparse.ArgumentParser(
        description="List CBMC coverage checking results."
    )

    optionst.coverage(parser)
    optionst.viewer_coverage(parser)
    optionst.srcdir(parser)
    optionst.log(parser)

    return parser

################################################################

def main():
    """List CBMC coverage checking results."""

    args = create_parser().parse_args()
    args = optionst.defaults(args)

    try:
        coveraget.make_and_save_coverage(args)
    except UserWarning as error:
        sys.exit(error)

if __name__ == "__main__":
    main()
