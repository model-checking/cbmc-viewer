#!/usr/bin/env python3

import argparse
import json
import sys

def create_parser():
    """Command line parser."""

    parser = argparse.ArgumentParser(
        description='Compare CBMC property checking results.'
    )

    parser.add_argument(
        'result1',
        help="""
        JSON result output of make-result or cbmc-viewer.
        """
    )
    parser.add_argument(
        'result2',
        help="""
        JSON result output of make-result or cbmc-viewer.
        """
    )

    return parser

def compare(result1, result2, full=False):
    try:
        dict1 = result1['viewer-result']
        dict2 = result2['viewer-result']

        keys = set([*dict1.keys(), *dict2.keys()])
        if not full:
            keys.remove('program')
            keys.remove('status')

        return all([dict1[key] == dict2[key] for key in keys])
    except KeyError:
        return False

################################################################

def main():
    """Compare CBMC property checking results."""

    args = create_parser().parse_args()

    with open(args.result1) as res1:
        result1 = json.load(res1)
    with open(args.result2) as res2:
        result2 = json.load(res2)

    if not compare(result1, result2):
        print('Results differ')
        sys.exit(1)

if __name__ == "__main__":
    main()
