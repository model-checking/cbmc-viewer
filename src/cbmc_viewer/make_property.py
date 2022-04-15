#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# -*- mode: python-mode -*-

"""Properties checked by CBMC during property checking."""

import argparse
import sys

from cbmc_viewer import optionst
from cbmc_viewer import propertyt

################################################################

def create_parser():
    """Command line parser."""

    parser = argparse.ArgumentParser(
        description='Properties checked by CBMC during property checking.'
    )

    optionst.property(parser)
    optionst.viewer_property(parser)
    optionst.srcdir(parser)
    optionst.log(parser)

    return parser

################################################################

def main():
    """Properties checked by CBMC during property checking."""

    args = create_parser().parse_args()
    args = optionst.defaults(args)

    try:
        properties = propertyt.make_property(args)
        print(properties)
    except UserWarning as error:
        sys.exit(error)

if __name__ == "__main__":
    main()
