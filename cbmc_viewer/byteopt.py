# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""CBMC byte extract and update operations.

This module displays all byte extract and update operations recorded by CBMC.
It includes SSA expression corresponding to an extract or update, source location
and the total number of extract/update operations.
Inputs to the module is a json file obtained by running CBMC with the
--show-byte-ops parse option, the project source and reporting directories.
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

VALID_BYTE_OP_LIST_ITEM = voluptuous.schema_builder.Schema({
    'sourceLocation': srcloct.VALID_SRCLOC,
    'ssaExprString': str
}, required=True)

VALID_BYTE_OP_SUMMARY = voluptuous.schema_builder.Schema({
    'summary': {
        'byteExtractList': [VALID_BYTE_OP_LIST_ITEM],
        'numOfExtracts': int,
        'byteUpdateList': [VALID_BYTE_OP_LIST_ITEM],
        'numOfUpdates': int
        }
}, required=True)

################################################################

class ByteOpSummary:

    def __init__(self, json_file, srcdir):

        self.summary = do_make_byteop(json_file, srcdir)
        self.validate()

    def __str__(self):
        """Render the byte op summary as html."""
        return templates.render_byteop_summary(self.summary)

    def validate(self):
        """Validate members of a summary object."""

        return voluptuous.humanize.validate_with_humanized_errors(
            self.__dict__, VALID_BYTE_OP_SUMMARY
        )

    def dump(self, filename=None, outdir='.'):
        """Write the byte op summary to a file rendered as html."""

        util.dump(self, filename or "byteop.html", outdir)

################################################################
# Json key tags to access elements in cbmc json output

JSON_EXTRACT_KEY = 'byteExtractStats'
JSON_EXTRACT_LIST_KEY = 'byteExtractList'
JSON_EXTRACT_COUNT_KEY = 'numOfExtracts'
JSON_UPDATE_KEY = 'byteUpdateStats'
JSON_UPDATE_LIST_KEY = 'byteUpdateList'
JSON_UPDATE_COUNT_KEY = 'numOfUpdates'
JSON_BYTE_OP_KEY = 'byteOpsStats'
JSON_SOURCE_LOC_KEY = 'sourceLocation'

################################################################
# Utility functions to generate byteop summary

def remove_ssa_expr(json_data):
    JSON_REMOVE_KEY = 'ssaExpr'

    json_extract_list = json_data.get(JSON_EXTRACT_KEY).get(JSON_EXTRACT_LIST_KEY)
    json_update_list = json_data.get(JSON_UPDATE_KEY).get(JSON_UPDATE_LIST_KEY)

    for item in json_extract_list:
        item.pop(JSON_REMOVE_KEY)
    for item in json_update_list:
        item.pop(JSON_REMOVE_KEY)

def get_src_location(json_data, root):
    json_extract_list = json_data.get(JSON_EXTRACT_KEY).get(JSON_EXTRACT_LIST_KEY)
    json_update_list = json_data.get(JSON_UPDATE_KEY).get(JSON_UPDATE_LIST_KEY)

    root = srcloct.abspath(root)
    for item in json_extract_list:
        item[JSON_SOURCE_LOC_KEY] = srcloct.json_srcloc(item[JSON_SOURCE_LOC_KEY], root)
    for item in json_update_list:
        item[JSON_SOURCE_LOC_KEY] = srcloct.json_srcloc(item[JSON_SOURCE_LOC_KEY], root)

def get_byte_op_metrics(json_file, root):
    summary = {}

    json_data = parse.parse_json_file(json_file)
    for item in json_data:
        if JSON_BYTE_OP_KEY in item.keys():
            byteop = item[JSON_BYTE_OP_KEY]
            remove_ssa_expr(byteop)
            get_src_location(byteop, root)

            summary.setdefault('byteExtractList',[]).extend(
                byteop[JSON_EXTRACT_KEY][JSON_EXTRACT_LIST_KEY])
            summary['numOfExtracts'] = summary.setdefault('numOfExtracts',0) + \
                byteop[JSON_EXTRACT_KEY][JSON_EXTRACT_COUNT_KEY]
            summary.setdefault('byteUpdateList',[]).extend(
                byteop[JSON_UPDATE_KEY][JSON_UPDATE_LIST_KEY])
            summary['numOfUpdates'] = summary.setdefault('numOfUpdates',0) + \
                byteop[JSON_UPDATE_KEY][JSON_UPDATE_COUNT_KEY]

    if not summary:
        summary = {
            'byteExtractList': [],
            'numOfExtracts': 0,
            'byteUpdateList': [],
            'numOfUpdates': 0
        }

    return summary

def fail(msg):
    """Log failure and raise exception."""

    logging.info(msg)
    raise UserWarning(msg)

def do_make_byteop(cbmc_byteop, srcdir):
    if srcdir and cbmc_byteop:
        if filet.is_json_file(cbmc_byteop):
            return get_byte_op_metrics(cbmc_byteop, srcdir)
        fail("Expected json file: {}"
            .format(cbmc_byteop))
