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

    optionst.result(parser)
    optionst.viewer_result(parser)
    optionst.log(parser)

    return parser

################################################################

def main():
    """List CBMC property checking results."""

    args = create_parser().parse_args()
    args = optionst.defaults(args)

    try:
        resultt.make_and_save_result(args)
    except UserWarning as error:
        sys.exit(error)

if __name__ == "__main__":
    main()
