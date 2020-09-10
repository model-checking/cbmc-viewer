# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""CBMC runtime analysis metric report.

This module collects all metric data across multiple proofs and
generates a single consolidated metric summary report./
"""

import os
import re
import json

import voluptuous
import voluptuous.humanize

from cbmc_viewer import filet
from cbmc_viewer import parse
from cbmc_viewer import templates
from cbmc_viewer import util

################################################################

VALID_BYTEOP_STATS = voluptuous.schema_builder.Schema({
    'numOfExtracts': int,
    'numOfUpdates': int,
    'link': str
    },required=True)

VALID_ALIAS_STATS = voluptuous.schema_builder.Schema({
    'max': int,
    'total': int,
    'link': str
    },required=True)

VALID_MEMOP_STATS = voluptuous.schema_builder.Schema({
    'count': int,
    'link': str
    },required=True)

VALID_ARRAY_CONSTRAINT_STATS = voluptuous.schema_builder.Schema({
    'count': int,
    'link': str
    },required=True)

VALID_CBMC_PROOF_STATS = voluptuous.schema_builder.Schema({
    'programSteps': int,
    'vccCount': int,
    'varCount': int,
    'clauseCount': int
    },required=True)

VALID_CLAUSE_STATS = voluptuous.schema_builder.Schema({
    'clauseCoreCount': int,
    'link': str
    },required=True)

VALID_RUNTIME_OBJ = voluptuous.schema_builder.Schema({
    'val': float,
    'string': str
    },required=True)

VALID_RUNTIME = voluptuous.schema_builder.Schema({
    'symex': VALID_RUNTIME_OBJ,
    'convertSSA': VALID_RUNTIME_OBJ,
    'postProc': VALID_RUNTIME_OBJ,
    'solver': VALID_RUNTIME_OBJ,
    'maxKey': {
        'val': str,
        'string': str
        }
    },required=True)

VALID_RUNTIME_ANALYSIS_SUMMARY = voluptuous.schema_builder.Schema([{
    'jobname': str,
    'link': str,
    'byteop': VALID_BYTEOP_STATS,
    'alias': VALID_ALIAS_STATS,
    'memop': VALID_MEMOP_STATS,
    'array': VALID_ARRAY_CONSTRAINT_STATS,
    'cbmc': VALID_CBMC_PROOF_STATS,
    'clause': VALID_CLAUSE_STATS,
    'runtimeKissat': float,
    'runtime': VALID_RUNTIME
    }],required=True)

VALID_SUMMARY = voluptuous.schema_builder.Schema({
    'summary': VALID_RUNTIME_ANALYSIS_SUMMARY
    },required=True)

################################################################

class RuntimeAnalysisSummary:

    def __init__(self, proofs, srcdir, outdir=None):
        self.summary = []

        for proof in proofs:
            jobname = proof
            proof_path = os.path.abspath(proof)
            outdir = outdir or os.path.join(proof_path, 'html', 'html')

            byteop = os.path.join(proof_path, 'html', 'json', 'viewer-byteop.json')
            alias = os.path.join(proof_path, 'html', 'json', 'viewer-alias.json')
            memop = os.path.join(proof_path, 'html', 'json', 'viewer-memop.json')
            array = os.path.join(proof_path, 'html', 'json', 'viewer-array.json')
            result = os.path.join(proof_path, 'html', 'json', 'viewer-result.json')
            clause = os.path.join(proof_path, 'html', 'json', 'viewer-core.json')
            kissat = os.path.join(proof_path, 'logs', 'kissat.txt')
            
            self.summary.append({
                'jobname': jobname,
                'link': get_link_to_job(outdir),
                'byteop': get_byteop_stats(byteop, outdir),
                'alias': get_alias_stats(alias, outdir),
                'memop': get_memop_stats(memop, outdir),
                'array': get_array_stats(array, outdir),
                'cbmc': get_cbmc_proof_stats(result),
                'clause': get_clause_stats(clause, outdir),
                'runtimeKissat': get_kissat_runtime(kissat),
                'runtime': get_cbmc_runtime_stats(result)
                })

        self.validate()


    def __str__(self):
        """Render the byte op summary as html."""
        return templates.render_runtime_analysis_summary(self.summary)

    def validate(self):
        """Validate members of a summary object."""

        return voluptuous.humanize.validate_with_humanized_errors(
            self.__dict__, VALID_SUMMARY
        )

    def dump(self, filename=None, outdir='.'):
        """Write the proof summary to a file rendered as html."""

        util.dump(self, filename or "runtime_analysis_report.html", outdir)

################################################################
# Utility functions to generate runtime analysis summary

def get_link(outdir, metric):
    return '<a href="{}/{}.html">'.format(outdir, metric)

def get_link_to_job(outdir):
    return get_link(outdir, 'index')

def fail(msg):
    """Log failure and raise exception."""

    logging.info(msg)
    raise UserWarning(msg)

def get_byteop_stats(file, outdir):
    byteop_link = get_link(outdir, 'byteop')

    if not filet.is_json_file(file):
        fail("Expected json file: {}"
            .format(file))

    json_data = parse.parse_json_file(file)
    byteop = {
        'numOfExtracts': json_data['numOfExtracts'],
        'numOfUpdates': json_data['numOfUpdates'],
        'link': byteop_link
    }

    return byteop

def get_alias_stats(file, outdir):
    alias_link = get_link(outdir, 'alias')

    if not filet.is_json_file(file):
        fail("Expected json file: {}"
            .format(file))

    json_data = parse.parse_json_file(file)
    alias = {
        'max': json_data['max'],
        'total': json_data['total'],
        'link': alias_link
    }

    return alias

def get_memop_stats(file, outdir):
    memop_link = get_link(outdir, 'memop')

    if not filet.is_json_file(file):
        fail("Expected json file: {}"
            .format(file))

    json_data = parse.parse_json_file(file)
    memop = {
        'count': json_data['count'],
        'link': memop_link
    }

    return memop

def get_array_stats(file, outdir):
    array_link = get_link(outdir, 'array')

    if not filet.is_json_file(file):
        fail("Expected json file: {}"
            .format(file))

    json_data = parse.parse_json_file(file)
    array = {
        'count': json_data['numOfConstraints'],
        'link': array_link
    }

    return array

def get_pattern(key):
    pattern_hash = {
        'programSteps': 'size of program expression: [0-9]+ steps',
        'vccCount': 'VCC\(s\), [0-9]+ remaining',
        'varCount': '[0-9]+ variables',
        'clauseCount': '[0-9]+ clauses',
        'symex': 'Runtime Symex: [0-9.]+',
        'convertSSA': 'Runtime Convert SSA: [0-9.]+',
        'postProc': 'Runtime Post-process: [0-9.]+',
        'solver': 'Runtime Solver: [0-9.]+'
    }

    return pattern_hash[key]

def cbmc_proof_stats_pattern_match(key, string):
    pattern = get_pattern(key)

    pattern_match = re.search(pattern, string)
    if pattern_match:
        count_match = re.search('[0-9]+', pattern_match.group(0))
        if count_match:
            count = count_match.group(0)
            return int(count), True
    return None, False

def cbmc_runtime_pattern_match(key, string):
    pattern = get_pattern(key)

    pattern_match = re.search(pattern, string)
    if pattern_match:
        time_match = re.search('[0-9.]+', pattern_match.group(0))
        if time_match:
            time = time_match.group(0)
            return float(time), True
    return None, False

def get_cbmc_proof_stats(file):
    if not filet.is_json_file(file):
        fail("Expected json file: {}"
            .format(file))

    json_data = parse.parse_json_file(file)
    result = json_data['viewer-result']['status']

    cbmc = {
        'programSteps': 0,
        'vccCount': 0,
        'varCount': 0,
        'clauseCount': 0
    }

    for line in result:
        for key in cbmc.keys():
            count, match = cbmc_proof_stats_pattern_match(key, line)
            if match:
                cbmc[key] += count

                if key == 'varCount':
                    continue
                else:
                    break

    return cbmc

def get_clause_stats(file, outdir):
    clause_link = get_link(outdir, 'clause')

    if not filet.is_json_file(file):
        fail("Expected json file: {}"
            .format(file))

    json_data = parse.parse_json_file(file)
    clause = {
        'clauseCoreCount': json_data['numOfClauses'],
        'link': clause_link
    }

    return clause

def get_kissat_runtime(file):

    if not filet.is_text_file(file):
        fail("Expected text file: {}"
            .format(file))
        
    with open(file) as f:
        for line in f.readlines():
            pattern = re.search('c process-time:.*[0-9.]+ seconds',line)
            if pattern:
                time_pat = re.search('[0-9.]+ seconds', pattern.group(0))
                time_pat = re.search('[0-9.]+', time_pat.group(0))
                if time_pat:
                    time = time_pat.group(0)
                    return float(time)
    return None

def get_cbmc_runtime_stats(file):
    if not filet.is_json_file(file):
        fail("Expected json file: {}"
            .format(file))

    json_data = parse.parse_json_file(file)
    result = json_data['viewer-result']['status']

    runtime = {
        'symex': {
            'val': 0.0,
            'string': "Symex"
            },
        'convertSSA': {
            'val': 0.0,
            'string': "SSA To SAT"
            },
        'postProc': {
            'val': 0.0,
            'string': "Post Processing"
            },
        'solver': {
            'val': 0.0,
            'string': "Solver"
            }
        }

    for line in result:
        for key in runtime.keys():
            time, match = cbmc_runtime_pattern_match(key, line)
            if match:
                runtime[key]['val'] += time
                break

    runtime_val = dict({key:runtime[key]['val'] for key in runtime.keys()})

    max_key = max(runtime_val, key=runtime_val.get)
    runtime['maxKey'] = {}
    runtime['maxKey']['val'] = max_key
    runtime['maxKey']['string'] = "Max Runtime Stage"

    return runtime

def create_parser():

    parser = argparse.ArgumentParser(
        description='Report CBMC results.'
    )

    parser.add_argument(
        '--json_files',
        default=[],
        nargs='+',
        help="""
        Provide list of json files.
        """,
        required=True)

    parser.add_argument(
        '--srcdir',
        help="""
        Project root directory.
        """,
        required=True)

    parser.add_argument(
        '--outdir',
        help="""
        Project output directory.
        """,
        required=True)

    return parser

def main():

    args = create_parser().parse_args()

    json_files = args.json_files
    srcdir = args.srcdir
    outdir = args.outdir

    RuntimeAnalysisSummary(json_files, srcdir).dump(outdir=outdir)

if __name__ == '__main__':
    main()