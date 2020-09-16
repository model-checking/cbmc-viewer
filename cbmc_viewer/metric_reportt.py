# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""CBMC runtime analysis metric report.

This module collects all metric data across multiple proofs and
generates a single consolidated metric summary report.
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

    def __init__(self, proofs, srcdir):
        self.summary = []

        for proof in proofs:
            jobname = proof
            proof_path = os.path.abspath(proof)
            outdir = os.path.join(proof_path, 'html', 'html')

            byteop = os.path.join(proof_path, 'html', 'json', 'viewer-byteop.json')
            alias = os.path.join(proof_path, 'html', 'json', 'viewer-alias.json')
            memop = os.path.join(proof_path, 'html', 'json', 'viewer-memop.json')
            array = os.path.join(proof_path, 'html', 'json', 'viewer-array.json')
            result = os.path.join(proof_path, 'html', 'json', 'viewer-result.json')
            clause = os.path.join(proof_path, 'html', 'json', 'viewer-clause.json')
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

    def dump(self, filename=None, outdir=None):
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

################################################################
# Byte extract/update metric

def get_byteop_stats(file, outdir):
    JSON_TAG = 'viewer-byteop'
    byteop_link = get_link(outdir, 'byteop')

    if not filet.is_json_file(file):
        fail("Expected json file: {}"
            .format(file))

    json_data = parse.parse_json_file(file)
    metric = json_data[JSON_TAG]['summary']
    byteop = {
        'numOfExtracts': metric['numOfExtracts'],
        'numOfUpdates': metric['numOfUpdates'],
        'link': byteop_link
    }

    return byteop

################################################################
# Points-to set metric

def get_alias_stats(file, outdir):
    JSON_TAG = 'viewer-alias'
    alias_link = get_link(outdir, 'alias')

    if not filet.is_json_file(file):
        fail("Expected json file: {}"
            .format(file))

    json_data = parse.parse_json_file(file)
    metric = json_data[JSON_TAG]
    alias = {
        'max': metric['max'],
        'total': metric['total'],
        'link': alias_link
    }

    return alias

################################################################
# Memory operation calls metric

def get_memop_stats(file, outdir):
    JSON_TAG = 'viewer-memop'
    memop_link = get_link(outdir, 'memop')

    if not filet.is_json_file(file):
        fail("Expected json file: {}"
            .format(file))

    json_data = parse.parse_json_file(file)
    metric = json_data[JSON_TAG]['summary']
    memop = {
        'count': metric['count'],
        'link': memop_link
    }

    return memop

################################################################
# Array constraint metric

def get_array_stats(file, outdir):
    JSON_TAG = 'viewer-array'
    array_link = get_link(outdir, 'array')

    if not filet.is_json_file(file):
        fail("Expected json file: {}"
            .format(file))

    json_data = parse.parse_json_file(file)
    metric = json_data[JSON_TAG]['summary']
    array = {
        'count': metric['numOfConstraints'],
        'link': array_link
    }

    return array

################################################################
# Solver query complexity metric

def get_clause_stats(file, outdir):
    JSON_TAG = 'viewer-clause'
    clause_link = get_link(outdir, 'clause')

    if not filet.is_json_file(file):
        fail("Expected json file: {}"
            .format(file))

    json_data = parse.parse_json_file(file)
    metric = json_data[JSON_TAG]['core']
    clause = {
        'clauseCoreCount': metric['numOfClauses'],
        'link': clause_link
    }

    return clause

################################################################
# CBMC proof and runtime metric

def get_pattern(key):
    pattern_hash = {
        # proof metrics
        'programSteps': 'size of program expression: [0-9]+ steps',
        'vccCount': 'VCC\(s\), [0-9]+ remaining',
        'varCount': '[0-9]+ variables',
        'clauseCount': '[0-9]+ clauses',
        # runtime metrics
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
    JSON_TAG = 'viewer-result'
    if not filet.is_json_file(file):
        fail("Expected json file: {}"
            .format(file))

    json_data = parse.parse_json_file(file)
    result = json_data[JSON_TAG]['status']

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

def get_cbmc_runtime_stats(file):
    JSON_TAG = 'viewer-result'
    if not filet.is_json_file(file):
        fail("Expected json file: {}"
            .format(file))

    json_data = parse.parse_json_file(file)
    result = json_data[JSON_TAG]['status']

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

################################################################
# Kissat runtime

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
