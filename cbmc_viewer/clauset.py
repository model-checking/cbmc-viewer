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

import voluptuous
import voluptuous.humanize

from cbmc_viewer import filet
from cbmc_viewer import parse
from cbmc_viewer import srcloct
from cbmc_viewer import templates
from cbmc_viewer import util

################################################################

VALID_CLAUSE = voluptuous.schema_builder.Schema({
    'GOTO': str,
    'GOTO_ID': int,
    'SAT_hardness': {
        'ClauseSet': [[int]],
        'Clauses': int,
        'Literals': int,
        'Variables': int
        },
    'SSA_expr': str,
    'Source': srcloct.VALID_SRCLOC
    },required=True)

VALID_SUMMARY = voluptuous.schema_builder.Schema({
    'summary': [VALID_CLAUSE],
    'core': {
        'instr': [int],
        'numOfInstr': int,
        'totalInstr': int,
        'numOfClauses': int
    },
    'instrNotInCore':[srcloct.VALID_SRCLOC],
    },required=True)

################################################################

class ClauseSummary:

    def __init__(self, json_file, srcdir, dimacs=None, core=None):
        core = core or json_file.replace("clause.json", "core")
        dimacs = dimacs or json_file.replace("clause.json", "dimacs.cnf")

        self.summary, clause_hash = do_make_clause(json_file, srcdir, dimacs)
        self.core = get_instr_in_core(core, clause_hash, len(self.summary))
        self.instrNotInCore = get_loc_not_in_core(self.summary, self.core['instr'])
        self.validate()


    def __str__(self):
        """Render the clause summary as html."""
        return templates.render_clause_summary(self.summary, self.core, self.instrNotInCore)

    def validate(self):
        """Validate members of a summary object."""

        return voluptuous.humanize.validate_with_humanized_errors(
            self.__dict__, VALID_SUMMARY
        )

    def dump(self, filename=None, outdir='.'):
        """Write the clause summary to a file rendered as html."""

        util.dump(self, filename or "clause.html", outdir)

################################################################
# Json key tags to access elements in cbmc json output

JSON_GOTO_ID_KEY = 'GOTO_ID'
JSON_SOURCE_LOC_KEY = 'Source'
JSON_SAT_HARDNESS_KEY = 'SAT_hardness'
JSON_CLAUSES_KEY = 'Clauses'
JSON_CLAUSE_SET_KEY = 'ClauseSet'

################################################################
# Utility functions to generate clause summary

def hash(clause):
    clause_hash_key = ''
    for lit in clause:
        clause_hash_key += str(lit) + ' '

    return clause_hash_key

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

def get_instr_in_core(core_file, clause_hash, instr_length):
    core_clauses = []
    instr_list = []
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

def get_src_location(json_data, root):
    root = srcloct.abspath(root)
    json_data[JSON_SOURCE_LOC_KEY] = \
        srcloct.json_srcloc(json_data[JSON_SOURCE_LOC_KEY], root)

    return json_data

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
        clause = get_src_location(clause, root)
        clause = get_clause_set(clause, clause_hash, dimacs_clause_list)

    return clauses, clause_hash

def fail(msg):
    """Log failure and raise exception."""

    logging.info(msg)
    raise UserWarning(msg)

def do_make_clause(cbmc_clause, srcdir, dimacs_file):
    if srcdir and cbmc_clause:
        if filet.is_json_file(cbmc_clause):
            return get_clause_metrics(cbmc_clause, srcdir, dimacs_file)
        fail("Expected json file: {}"
             .format(cbmc_clause))
