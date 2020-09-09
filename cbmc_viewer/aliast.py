# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""CBMC points-to set metric.

This module displays the size and contents of the points-to sets for
pointer dereferencing in CBMC. The module also calculates and displays
the number of dereferences of a pointer.
Inputs to the module is a json file obtained by running CBMC with the
--show-points-to-sets parse option and the project reporting directory.
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

VALID_ALIAS_ITEM = voluptuous.schema_builder.Schema({
    'PointsToSetSize': int,
    'PointsToSet': list,
    'RetainedValuesSetSize': int, # subset of points-to sets
    'RetainedValuesSet': list,
    'Value': str,
    'numOfDeref': int
    },required=True)

VALID_ALIAS = voluptuous.schema_builder.Schema({
    str : VALID_ALIAS_ITEM # str here stores the pointer variable
    })

VALID_SUMMARY = voluptuous.schema_builder.Schema({
    'summary': VALID_ALIAS,
    'max': int,
    'total': int
    },required=True)

################################################################

class AliasSummary:

    def __init__(self, json_file):
        self.summary = do_make_alias(json_file)
        self.max, self.total = get_max_total(self.summary)
        self.validate()

    def __str__(self):
        """Render the points-to set summary as html."""
        return templates.render_alias_summary(self)

    def validate(self):
        """Validate members of a summary object."""

        return voluptuous.humanize.validate_with_humanized_errors(
            self.__dict__, VALID_SUMMARY
        )

    def dump(self, filename=None, outdir='.'):
        """Write the points-to set summary to a file rendered as html."""

        util.dump(self, filename or "alias.html", outdir)

################################################################
# Json key tags to access elements in cbmc json output

JSON_POINTS_TO_SET_SIZE_KEY = 'PointsToSetSize'
JSON_POINTER_KEY = 'Pointer'

################################################################
# Utility functions to generate byteop summary

def get_max_total(alias_summary):
    max_val = 0
    total = 0
    for alias_item in alias_summary.items():
        if int(alias_item[1][JSON_POINTS_TO_SET_SIZE_KEY]) > max_val:
            max_val = int(alias_item[1][JSON_POINTS_TO_SET_SIZE_KEY])
        total += int(alias_item[1][JSON_POINTS_TO_SET_SIZE_KEY]) * alias_item[1]['numOfDeref']

    return max_val, total

def get_alias_item(json_item):
    pointer = json_item[JSON_POINTER_KEY]
    json_item.pop(JSON_POINTER_KEY)
    json_item.update({"numOfDeref": 1})

    alias_item = {}
    alias_item[pointer] = json_item

    return alias_item

def is_equal(summary, item):
    for key in item.keys():
        if key in summary.keys():
            is_equal_return = all([item[key][k] == summary[key][k] for k in item[key].keys() if k not in ['numOfDeref']])
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
            return get_alias_metrics(cbmc_alias)
        fail("Expected json file: {}"
             .format(cbmc_alias))
