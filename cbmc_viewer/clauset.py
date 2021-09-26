# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""CBMC solver query complexity metric.

This module displays mapping between clauses and program code.
It includes SSA expression corresponding to the line of code, respective
clauses and the number of clauses, variables and literals for the LOC.
Additionally, it tracks clauses in the UNSAT core and displays LOC that do
not contribute any clauses to the core.
Inputs to the module is a json file obtained by running CBMC with the
--write-solver-stats-to parse option, dimacs formula from --dimacs CBMC
option, the UNSAT core obtained by running kissat (to get proof of UNSAT)
and then drat-trim (extracts the core), the project source and reporting
directories.
"""

import logging
import json

import voluptuous
import voluptuous.humanize

from cbmc_viewer import filet
from cbmc_viewer import parse
from cbmc_viewer import srcloct
from cbmc_viewer import templates
from cbmc_viewer import util

JSON_TAG = "viewer-clause"

################################################################

VALID_CLAUSE = voluptuous.schema_builder.Schema({
    'GOTO': str, # string storing the goto instruction
    'GOTO_ID': int, # goto instrucion ID as assigned by CBMC for the above instruction
    'SAT_hardness': { # stores solver complexity stats for this instruction
        'ClauseSet': [[int]],
        'Clauses': int,
        'Literals': int,
        'Variables': int
        },
    'SSA_expr': str,
    'Source': srcloct.VALID_SRCLOC
    },required=True)

VALID_CLAUSE_SUMMARY = voluptuous.schema_builder.Schema({
    'summary': [VALID_CLAUSE], # list of instructions with the corresponding solver query stats
    'core': {
        'instr': [int], # list of goto ID of instructions that contribute to core
        'numOfInstr': int, # num of instr that contribute to core
        'totalInstr': int, # total num of instructions in summary
        'numOfClauses': int # num of clauses in core
    },
    'instrNotInCore':[srcloct.VALID_SRCLOC], # lines of code that don't have any instructions contributing to the core
    },required=True)

################################################################

class ClauseSummary:

    def __init__(self, json_file, srcdir, dimacs=None, core=None):
        core = core or json_file.replace("clause.json", "core")
        dimacs = dimacs or json_file.replace("clause.json", "dimacs.cnf")

        self.summary, clause_hash = get_clause_metrics(json_file, srcdir, dimacs)
        self.core = get_instr_in_core(core, clause_hash, len(self.summary))
        self.instrNotInCore = get_loc_not_in_core(self.summary, self.core['instr'])
        self.validate()

    def __repr__(self):
        """A dict representation of clause summary."""

        self.validate()
        return self.__dict__

    def __str__(self):
        """A string representation of clause summary."""

        return json.dumps({JSON_TAG: self.__repr__()}, indent=2)

    def validate(self):
        """Validate members of a summary object."""

        return voluptuous.humanize.validate_with_humanized_errors(
            self.__dict__, VALID_CLAUSE_SUMMARY
        )

    def dump(self, filename=None, outdir=None):
        """Write byteop metrics to a file or stdout."""

        util.dump(self, filename, outdir)

    def render_report(self, filename=None, outdir=None):
        """Write the clause summary to a file rendered as html."""

        clause_html = templates.render_clause_summary(self.summary,
                                                      self.core,
                                                      self.instrNotInCore)
        util.dump(clause_html, filename or "clause.html", outdir)

################################################################
# Json key tags to access elements in cbmc json output

JSON_GOTO_ID_KEY = 'GOTO_ID'
JSON_SOURCE_LOC_KEY = 'Source'
JSON_SAT_HARDNESS_KEY = 'SAT_hardness'
JSON_CLAUSES_KEY = 'Clauses'
JSON_CLAUSE_SET_KEY = 'ClauseSet'

# Example cbmc json output
# [
#   {
#     "GOTO": "// Labels: __CPROVER_HIDE__CPROVER_initialize();",
#     "GOTO_ID": 0,
#     "SAT_hardness": {
#       "ClauseSet": [ ],
#       "Clauses": 0,
#       "Literals": 0,
#       "Variables": 0
#     },
#     "SSA_expr": "true",
#     "Source": {}
#   },
#   ...
#   {
#     "GOTO": "ASSERT main::1::a[cast(1, signedbv[64])] < 10",
#     "GOTO_ID": 95,
#     "SAT_hardness": {
#       "ClauseSet": [ 6, 7, 8 ... ],
#       "Clauses": 134,
#       "Literals": 459,
#       "Variables": 67
#     },
#     "SSA_expr": "¬(main::1::a!0@1#3[1] ≥ 10)",
#     "Source": {
#       "file": "simple_main.c",
#       "function": "main",
#       "line": "21",
#       "workingDirectory": "..."
#     }
#   }
# ]

################################################################
# Utility functions to generate clause summary

def hash(clause):
    # returns string format of clause to be used as hash key
    return ' '.join([str(lit) for lit in clause])

def get_loc_not_in_core(summary, core_instr):
    instrNotInCore = []
    coreSourceList = []
    for instr in summary:
        if instr[JSON_GOTO_ID_KEY] in core_instr:
            coreSourceList.append(instr[JSON_SOURCE_LOC_KEY])

    for instr in summary:
        if instr[JSON_SAT_HARDNESS_KEY][JSON_CLAUSES_KEY] > 0:
            if instr[JSON_SOURCE_LOC_KEY] not in coreSourceList:
                if instr[JSON_SOURCE_LOC_KEY] not in instrNotInCore:
                    instrNotInCore.append(instr[JSON_SOURCE_LOC_KEY])

    return instrNotInCore

# core_file: file storing the UNSAT core
# clause_hash: mapping between clauses and goto intruction ID
# instr_length: total number of instructions in the CBMC json output
def get_instr_in_core(core_file, clause_hash, instr_length):
    core_clauses = [] # clauses in core; clause is a list of literals
    instr_list = [] # list of goto ID of instructions in core
    keys = clause_hash.keys()

    try:
        with open(core_file) as f:
            for line in f.readlines():
                if "p cnf" in line:
                    continue

                clause = [int(lit) for lit in line.split(' ')]
                core_clauses.append(clause)

                clause.sort()
                clause_hash_key = hash(clause)

                if clause_hash_key in keys:
                    instr = clause_hash[clause_hash_key]
                    for i in instr:
                        instr_list.append(i)

    except IOError as err:
        fail("Core file not found: {}"
            .format(core_file))

    instr_list = list(set(instr_list))
    instr_list.sort()

    core_instr = {
        'instr': instr_list,
        'numOfInstr': len(instr_list),
        'totalInstr': instr_length,
        'numOfClauses': len(core_clauses)}

    return core_instr

def update_src_location_format(json_data, root):
    root = srcloct.abspath(root)
    json_data[JSON_SOURCE_LOC_KEY] = \
        srcloct.json_srcloc(json_data[JSON_SOURCE_LOC_KEY], root)

def get_clause_set(json_data, clause_hash, dimacs_clause_list):
    clause_count = json_data[JSON_SAT_HARDNESS_KEY][JSON_CLAUSES_KEY]
    if clause_count == 0:
        return json_data

    clause_id_set = json_data[JSON_SAT_HARDNESS_KEY][JSON_CLAUSE_SET_KEY]
    goto_id = json_data[JSON_GOTO_ID_KEY]

    clause_set = []
    for clause_id in clause_id_set:
        clause = \
            [int(lit) for lit in dimacs_clause_list[clause_id].split(' ')]
        clause.sort()
        clause_set.append(clause)

        clause_hash.setdefault(hash(clause), []).append(goto_id)

    json_data[JSON_SAT_HARDNESS_KEY][JSON_CLAUSE_SET_KEY] = clause_set

    return json_data

def get_clause_metrics(json_file, root, dimacs_file):
    clause_hash = {} # hash map of clauses to goto instructions

    dimacs_clause_list = []
    try:
        with open(dimacs_file) as f:
            dimacs_clause_list = f.readlines()

    except IOError as err:
        fail("Dimacs file not found: {}"
            .format(dimacs_file))

    clauses = parse.parse_json_file(json_file)
    for clause in clauses:
        update_src_location_format(clause, root)
        clause = get_clause_set(clause, clause_hash, dimacs_clause_list)

    return clauses, clause_hash

def fail(msg):
    """Log failure and raise exception."""

    logging.info(msg)
    raise UserWarning(msg)

def do_make_clause(cbmc_clause, srcdir, dimacs_file=None, core_file=None):
    if srcdir and cbmc_clause:
        if filet.is_json_file(cbmc_clause):
            return ClauseSummary(cbmc_clause, srcdir, dimacs_file, core_file)
        fail("Expected json file: {}"
             .format(cbmc_clause))
