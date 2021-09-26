# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""CBMC points-to set metric.

This module displays the size and contents of the points-to sets for
pointer dereferencing in CBMC (pointer aliasing metric). The module 
also calculates and displays the number of dereferences of a pointer.
Inputs to the module is a json file obtained by running CBMC with the
--show-points-to-sets parse option and the project reporting directory.
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

JSON_TAG = "viewer-alias"

################################################################

VALID_ALIAS_ITEM = voluptuous.schema_builder.Schema({
    'PointsToSetSize': int,
    'PointsToSet': list,
    'RetainedValuesSetSize': int, # subset of points-to sets
    'RetainedValuesSet': list,
    'Value': str,
    'numOfDeref': int
    },required=True)

VALID_ALIAS = voluptuous.schema_builder.Schema({
    str : VALID_ALIAS_ITEM # str here stores the pointer variable name
    })

VALID_ALIAS_SUMMARY = voluptuous.schema_builder.Schema({
    'summary': VALID_ALIAS,
    'max': int, # max points-to set size
    'total': int # total = sum(points_to_set_size * num_of_deref)
    },required=True)

################################################################

class AliasSummary:

    def __init__(self, json_file):
        self.summary = get_alias_metrics(json_file)
        self.max, self.total = get_max_total(self.summary)
        self.validate()

    def __repr__(self):
        """A dict representation of alias summary."""

        self.validate()
        return self.__dict__

    def __str__(self):
        """A string representation of alias summary."""

        return json.dumps({JSON_TAG: self.__repr__()}, indent=2)

    def validate(self):
        """Validate members of a summary object."""

        return voluptuous.humanize.validate_with_humanized_errors(
            self.__dict__, VALID_ALIAS_SUMMARY
        )

    def dump(self, filename=None, outdir=None):
        """Write the alias summary to a file or stdout."""

        util.dump(self, filename, outdir)

    def render_report(self, filename=None, outdir=None):
        """Write the alias summary to a file rendered as html."""

        alias_html = templates.render_alias_summary(self)
        util.dump(alias_html, filename or "alias.html", outdir)

################################################################
# Json key tags to access elements in cbmc json output

JSON_POINTS_TO_SET_SIZE_KEY = 'PointsToSetSize'
JSON_POINTER_KEY = 'Pointer'

# Example cbmc json output
# [
#   {
#     "program": "CBMC 5.13.0 (cbmc-5.13.1-44-g31340ca28)"
#   },
#   ...
#   {
#     "Pointer": "main::1::foo_p!0@1",
#     "PointsToSet": [ ],
#     "PointsToSetSize": 0,
#     "RetainedValuesSet": [ ],
#     "RetainedValuesSetSize": 0,
#     "Value": "main::1::foo_p$object"
#   },
#   {
#     "Pointer": "main::1::foo_p$object..next",
#     "PointsToSet": [ "unknown" ],
#     "PointsToSetSize": 1,
#     "RetainedValuesSet": [ "unknown" ],
#     "RetainedValuesSetSize": 1,
#     "Value": "symex::invalid_object"
#   },
#   ...
#   {
#     "cProverStatus": "..."
#   }
# ]

################################################################
# Utility functions to generate alias summary

def get_max_total(alias_summary):
    max_val = 0
    total = 0
    for pointer, data in alias_summary.items():
        if int(data[JSON_POINTS_TO_SET_SIZE_KEY]) > max_val:
            max_val = int(data[JSON_POINTS_TO_SET_SIZE_KEY])
        total += int(data[JSON_POINTS_TO_SET_SIZE_KEY]) * \
            data['numOfDeref']

    return max_val, total

def get_alias_item(json_item):
    pointer = json_item[JSON_POINTER_KEY]
    json_item.pop(JSON_POINTER_KEY)
    json_item.update({"numOfDeref": 1})

    return {pointer: json_item}

def is_equal(summary, item):
    for key in item.keys():
        if key in summary.keys():
            is_equal_return = all([item[key][k] == summary[key][k]
                for k in item[key].keys() if k not in ['numOfDeref']])
            if(is_equal_return):
                summary[key]['numOfDeref'] += 1
            return is_equal_return
        else:
            return False;

def get_alias_metrics(json_file):
    summary = {}

    json_data = parse.parse_json_file(json_file)
    for item in json_data:
        if JSON_POINTER_KEY in item.keys():
            alias_item = get_alias_item(item)
            if not summary:
                summary.update(alias_item)
                continue

            if not is_equal(summary, alias_item):
                summary.update(alias_item)

    return summary

def fail(msg):
    """Log failure and raise exception."""

    logging.info(msg)
    raise UserWarning(msg)

def do_make_alias(cbmc_alias):
    if cbmc_alias:
        if filet.is_json_file(cbmc_alias):
            return AliasSummary(cbmc_alias)
        fail("Expected json file: {}"
             .format(cbmc_alias))
