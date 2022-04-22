# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Main entry point for cbmc-viewer and subcommands."""

from cbmc_viewer import optionst

def main():
    """Construct the cbmc report."""

    args = optionst.create_parser().parse_args()
    args = optionst.defaults(args)
    args.func(args)
