# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""CBMC memory operation metric.

This module displays calls to memory operations: memcpy, memcmp, memmove,
memset, memchr, memccpy. It include SSA the function call expression,
source location and total number of calls to these operations.
Inputs to the module is a json file obtained by running CBMC with the
--show-goto-functions parse option, the project source and reporting
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

VALID_MEMOP = voluptuous.schema_builder.Schema({
    'funcCall': str,
    'sourceLoc': srcloct.VALID_SRCLOC
    },required=True)

VALID_SUMMARY = voluptuous.schema_builder.Schema({
    'summary': {
        'list': [VALID_MEMOP],
        'count': int}
    },required=True)

################################################################

class MemOpSummary:

    def __init__(self, json_file, srcdir):
        self.summary = do_make_memop(json_file, srcdir)
        self.validate()


    def __str__(self):
        """Render the memory op call summary as html."""
        return templates.render_memop_summary(self.summary)

    def validate(self):
        """Validate members of a summary object."""

        return voluptuous.humanize.validate_with_humanized_errors(
            self.__dict__, VALID_SUMMARY
        )

    def dump(self, filename=None, outdir='.'):
        """Write the memory op call summary to a file rendered as html."""

        util.dump(self, filename or "memop.html", outdir)

################################################################
# Json key tags to access elements in cbmc json output

JSON_FUNCTIONS_KEY = 'functions'
JSON_BODY_AVAIL_KEY = 'isBodyAvailable'
JSON_INSTRUCTIONS_KEY = 'instructions'
JSON_INSTRUCTION_ID_KEY = 'instructionId'
JSON_OPERANDS_KEY = 'operands'
JSON_FUNCTION_INSTR_KEY = 'instruction'
JSON_SOURCE_LOC_KEY = 'sourceLocation'

# Json keys for CBMC operands
JSON_ID_KEY = 'id'
JSON_NAMED_SUB_KEY = 'namedSub'
JSON_IDENTIFIER_KEY = 'identifier'

# List of memory operations
list_mem_func = ["memcmp","memcpy","memmove","memset","memccpy","memchr"]

################################################################
# Utility functions to generate memory op call summary

def get_src_location(json_data, root):
    root = srcloct.abspath(root)
    json_data['sourceLoc'] = \
        srcloct.json_srcloc(json_data['sourceLocation'], root)

    return json_data

def is_memop_call(operands):
    for item in operands:
        if item[JSON_ID_KEY] == "symbol":
            func_name = \
                item[JSON_NAMED_SUB_KEY][JSON_IDENTIFIER_KEY][JSON_ID_KEY]
            return any([True for func in list_mem_func if func in func_name])

    return False

def get_func_call(instr):
    # str_list[0] is location, str_list[1] is the call
    str_list = instr.split('\n')
    func_call = str_list[1].strip()
    return func_call

def get_memop_metrics(json_file, srcdir):
    summary = {
        'list': [],
        'count': 0
    }

    json_data = parse.parse_json_file(json_file)
    for item in json_data:
        if JSON_FUNCTIONS_KEY in item.keys():
            functions = item[JSON_FUNCTIONS_KEY]
            break

    for func in functions:
        if func[JSON_BODY_AVAIL_KEY]:
            instructions = func[JSON_INSTRUCTIONS_KEY]
            for instr in instructions:
                if instr[JSON_INSTRUCTION_ID_KEY] == "FUNCTION_CALL":
                    if is_memop_call(instr[JSON_OPERANDS_KEY]):
                        memop_call_json = {
                            'funcCall': \
                                get_func_call(
                                    instr[JSON_FUNCTION_INSTR_KEY]),
                            'sourceLoc': \
                                srcloct.json_srcloc(
                                    instr[JSON_SOURCE_LOC_KEY], srcdir)}

                        summary['list'].append(memop_call_json)

    summary['count'] = len(summary['list'])

    return summary

def fail(msg):
    """Log failure and raise exception."""

    logging.info(msg)
    raise UserWarning(msg)

def do_make_memop(cbmc_memop, srcdir):
    if srcdir and cbmc_memop:
        if filet.is_json_file(cbmc_memop):
            return get_memop_metrics(cbmc_memop, srcdir)
        fail("Expected json file: {}"
             .format(cbmc_memop))
