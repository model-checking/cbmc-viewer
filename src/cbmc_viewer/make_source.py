#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# -*- mode: python-mode -*-

"""List the source files used to build a goto binary."""

import argparse
import sys

from cbmc_viewer import optionst
from cbmc_viewer import sourcet

################################################################

def create_parser():
    """Command line parser."""

    parser = argparse.ArgumentParser(
        description='List the source files used to build a goto binary.')

    optionst.viewer_source(parser)
    optionst.goto(parser)
    optionst.srcdir(parser)
    optionst.wkdir(parser)
    optionst.source_method(parser)
    optionst.extensions(parser)
    optionst.exclude(parser)
    optionst.log(parser)

    return parser

################################################################

def main():
    """List the source files used to build a goto binary."""

    args = create_parser().parse_args()
    args = optionst.defaults(args)

    try:
        sources = sourcet.make_source(args)
        print(sources)
    except UserWarning as error:
        sys.exit(error)

################################################################

if __name__ == '__main__':
    main()
