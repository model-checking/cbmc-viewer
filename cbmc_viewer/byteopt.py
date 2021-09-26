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
import json

import voluptuous
import voluptuous.humanize

from cbmc_viewer import filet
from cbmc_viewer import parse
from cbmc_viewer import srcloct
from cbmc_viewer import templates
from cbmc_viewer import util

JSON_TAG = "viewer-byteop"

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

        self.summary = get_byte_op_metrics(json_file, srcdir)
        self.validate()

    def __repr__(self):
        """A dict representation of byte op summary."""

        self.validate()
        return self.__dict__

    def __str__(self):
        """A string representation of byte op summary."""

        return json.dumps({JSON_TAG: self.__repr__()}, indent=2)

    def validate(self):
        """Validate members of a summary object."""

        return voluptuous.humanize.validate_with_humanized_errors(
            self.__dict__, VALID_BYTE_OP_SUMMARY
        )

    def dump(self, filename=None, outdir=None):
        """Write byteop metrics to a file or stdout."""

        util.dump(self, filename, outdir)

    def render_report(self, filename=None, outdir=None):
        """Write the byte op summary to a file rendered as html."""

        byteop_html = templates.render_byteop_summary(self.summary)
        util.dump(byteop_html, filename or "byteop.html", outdir)

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

# Example cbmc json output
# [
#   {
#     "program": "CBMC 5.13.0 (cbmc-5.13.1-44-g31340ca28)"
#   },
#   ...
#   {
#     "byteOpsStats": {
#       "byteExtractStats": {
#         "byteExtractList": [ ],
#         "numOfExtracts": 0
#       },
#       "byteUpdateStats": {
#         "byteUpdateList": [ ],
#         "numOfUpdates": 0
#       }
#     }
#   },
#   ...
#   {
#     "byteOpsStats": {
#       "byteExtractStats": {
#         "byteExtractList": [
#           {
#             "sourceLocation": {
#               "file": "byte_extract_code.c",
#               "function": "main",
#               "line": "12",
#               "workingDirectory": "..."
#             },
#             "ssaExpr": {...},
#             "ssaExprString": "... byte_update_little_endian ..."
#           }
#         ],
#         "numOfExtracts": 1
#       },
#       "byteUpdateStats": {
#         "byteUpdateList": [
#           {
#             "sourceLocation": {
#               "file": "byte_extract_code.c",
#               "function": "main",
#               "line": "12",
#               "workingDirectory": "..."
#             },
#             "ssaExpr": {...},
#             "ssaExprString": "... byte_update_little_endian ..."
#           }
#         ],
#         "numOfUpdates": 1
#       }
#     }
#   },
#   ...
#   {
#     "messageText": "...",
#     "messageType": "STATUS-MESSAGE"
#   }
# ]

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

def update_src_location_format(json_data, root):
    json_extract_list = json_data.get(JSON_EXTRACT_KEY).get(JSON_EXTRACT_LIST_KEY)
    json_update_list = json_data.get(JSON_UPDATE_KEY).get(JSON_UPDATE_LIST_KEY)

    root = srcloct.abspath(root)
    for item in json_extract_list:
        item[JSON_SOURCE_LOC_KEY] = srcloct.json_srcloc(item[JSON_SOURCE_LOC_KEY], root)
    for item in json_update_list:
        item[JSON_SOURCE_LOC_KEY] = srcloct.json_srcloc(item[JSON_SOURCE_LOC_KEY], root)

def get_byte_op_metrics(json_file, root):
    summary = {
        'byteExtractList': [],
        'numOfExtracts': 0,
        'byteUpdateList': [],
        'numOfUpdates': 0
    }

    json_data = parse.parse_json_file(json_file)
    for item in json_data:
        if JSON_BYTE_OP_KEY in item.keys():
            byteop = item[JSON_BYTE_OP_KEY]
            remove_ssa_expr(byteop)
            update_src_location_format(byteop, root)

            summary['byteExtractList'].extend(
                byteop[JSON_EXTRACT_KEY][JSON_EXTRACT_LIST_KEY])
            summary['numOfExtracts'] += \
                byteop[JSON_EXTRACT_KEY][JSON_EXTRACT_COUNT_KEY]
            summary['byteUpdateList'].extend(
                byteop[JSON_UPDATE_KEY][JSON_UPDATE_LIST_KEY])
            summary['numOfUpdates'] += \
                byteop[JSON_UPDATE_KEY][JSON_UPDATE_COUNT_KEY]

    return summary

def fail(msg):
    """Log failure and raise exception."""

    logging.info(msg)
    raise UserWarning(msg)

def do_make_byteop(cbmc_byteop, srcdir):
    if srcdir and cbmc_byteop:
        if filet.is_json_file(cbmc_byteop):
            return ByteOpSummary(cbmc_byteop, srcdir)
        fail("Expected json file: {}"
            .format(cbmc_byteop))
