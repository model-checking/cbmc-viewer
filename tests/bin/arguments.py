# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Methods for common command-line argument parsing."""

import argparse
import logging

def create_parser(options=None, description=None):
    """Create a parser for command line arguments."""

    options = options or []
    description = description or ""

    flags = [option.get('flag') for option in options]
    if '--verbose' not in flags:
        options.append({'flag': '--verbose', 'action': 'store_true', 'help': 'Verbose output'})
    if '--debug' not in flags:
        options.append({'flag': '--debug', 'action': 'store_true', 'help': 'Debug output'})

    parser = argparse.ArgumentParser(description=description)
    for option in options:
        flag = option.pop('flag')
        parser.add_argument(flag, **option)
    return parser

def configure_logging(args):
    """Configure logging level based on command line arguments."""

    # Logging is configured by first invocation of basicConfig
    fmt = '%(levelname)s: %(message)s'
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format=fmt)
        return
    if args.verbose:
        logging.basicConfig(level=logging.INFO, format=fmt)
        return
    logging.basicConfig(format=fmt)
