#!/usr/bin/env python3

import argparse
import json
import sys
import subprocess

def create_parser():
    """Command line parser."""

    parser = argparse.ArgumentParser(
        description='Compare CBMC coverage checking results.'
    )

    parser.add_argument(
        'coverage1',
        help="""
        JSON coverage output of make-coverage or cbmc-viewer.
        """
    )
    parser.add_argument(
        'coverage2',
        help="""
        JSON coverage output of make-coverage or cbmc-viewer.
        """
    )
    return parser

def dict_diff(dict1, dict2):
        with open('/tmp/coverage1.json', 'w') as out1:
            print(json.dumps(dict1, indent=2, sort_keys=True), file=out1)
        with open('/tmp/coverage2.json', 'w') as out2:
            print(json.dumps(dict2, indent=2, sort_keys=True), file=out2)

        proc = subprocess.run(
            ['diff', '/tmp/coverage1.json', '/tmp/coverage2.json'],
            text=True,
            capture_output=True,
            check=False
        )
        return proc.stdout

def diff(coverage1, coverage2):
    try:
        dict1 = coverage1['viewer-coverage']['line_coverage']
        dict2 = coverage2['viewer-coverage']['line_coverage']

        dict1_missing = []
        dict2_missing = []
        difference = {}

        for key in set([*dict1.keys(), *dict2.keys()]):
            if key not in dict1:
                dict1_missing.append(key)
                continue
            if key not in dict2:
                dict2_missing.append(key)
                continue

            idict1 = {int(line): value for line, value in dict1[key].items()}
            with open('/tmp/coverage1.json', 'w') as out1:
                print(json.dumps(idict1, indent=2, sort_keys=True), file=out1)

            idict2 = {int(line): value for line, value in dict2[key].items()}
            with open('/tmp/coverage2.json', 'w') as out2:
                print(json.dumps(idict2, indent=2, sort_keys=True), file=out2)

            proc = subprocess.run(
                ['diff', '/tmp/coverage1.json', '/tmp/coverage2.json'],
                text=True,
                capture_output=True,
                check=False
            )
            if proc.stdout:
                difference[key] = proc.stdout

        if not dict1_missing and not dict2_missing and not difference:
            return {}

        return {'left-missing': sorted(dict1_missing),
                'right-missing': sorted(dict2_missing),
                'difference': {key: value
                               for key, value in sorted(difference.items())}
                }
    except KeyError:
        raise UserWarning("Diff computation failed.")

def compare(coverage1, coverage2, full=False, verbose=True):
    try:
        dict1 = coverage1['viewer-coverage']
        dict2 = coverage2['viewer-coverage']

        if full:
            return dict1 == dict2

        return dict1["line_coverage"] == dict2["line_coverage"]
    except KeyError:
        return False

################################################################

def main():
    """Compare CBMC coverage checking results."""

    args = create_parser().parse_args()

    with open(args.coverage1) as res1:
        coverage1 = json.load(res1)
    with open(args.coverage2) as res2:
        coverage2 = json.load(res2)

    res = diff(coverage1, coverage2)
    if res:
        if 'left_missing' in res:
            print('Files missing from {}'.format(args.coverage1))
            print(json.dumps(res['left_missing'], indent=2))
        if 'right_missing' in res:
            print('Files missing from {}'.format(args.coverage2))
            print(json.dumps(res['right_missing'], indent=2))
        if 'difference' in res:
            for key in sorted(res['difference'].keys()):
                print(key)
                print(res['difference'][key])

if __name__ == "__main__":
    main()
