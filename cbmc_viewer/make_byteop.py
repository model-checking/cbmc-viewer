#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# -*- mode: python-mode -*-

"""List CBMC Byte Extract/Update metrics."""


import argparse
import sys
import os

from cbmc_viewer import byteopt
from cbmc_viewer import optionst

def create_parser():
    """Command line parser."""

    parser = argparse.ArgumentParser(
        description="List CBMC byte extract and update metrics."
    )

    optionst.byteop(parser)
    optionst.srcdir(parser)
    optionst.reportdir(parser)

    optionst.log(parser)

    return parser

################################################################

def main():
    """List CBMC byte extract and update metrics."""

    args = create_parser().parse_args()
    args = optionst.defaults(args)

    try:
        byteop = byteopt.ByteOpSummary(args.byteop,
                                       args.srcdir)

        htmldir = os.path.join(args.reportdir, "html")
        jsondir = os.path.join(args.reportdir, "json")

        byteop.dump(filename='viewer-byteop', outdir=jsondir)
        byteop.render_report(outdir=htmldir)
    except UserWarning as error:
        sys.exit(error)

if __name__ == "__main__":
    main()
