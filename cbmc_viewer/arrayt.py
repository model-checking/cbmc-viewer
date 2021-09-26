# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""CBMC Array Constraints.

This module displays count of different types of array constraints
added during postprocessing.
Inputs to the module is a json file obtained by running CBMC with the
--show-array-constraints parse option and the project reporting
directory.
"""
import logging
import json

import voluptuous
import voluptuous.humanize

from cbmc_viewer import filet
from cbmc_viewer import parse
from cbmc_viewer import templates
from cbmc_viewer import util

JSON_TAG = "viewer-array"

################################################################

VALID_CONSTRAINT = voluptuous.schema_builder.Schema({
    str: int # example: arrayWith, arrayAckermann
    })

VALID_ARRAY_CONSTRAINTS = voluptuous.schema_builder.Schema({
    'arrayConstraints': VALID_CONSTRAINT,
    'numOfConstraints': int
    },required=True)

VALID_ARRAY_CONSTRAINT_SUMMARY = voluptuous.schema_builder.Schema({
    'summary': VALID_ARRAY_CONSTRAINTS
    },required=True)

################################################################

class ArrayConstraintSummary:

    def __init__(self, json_file):
        self.summary = get_array_constraint_metrics(json_file)
        self.validate()

    def __repr__(self):
        """A dict representation of array constraint summary."""

        self.validate()
        return self.__dict__

    def __str__(self):
        """A string representation of array constraint summary."""

        return json.dumps({JSON_TAG: self.__repr__()}, indent=2)

    def validate(self):
        """Validate members of a summary object."""

        return voluptuous.humanize.validate_with_humanized_errors(
            self.__dict__, VALID_ARRAY_CONSTRAINT_SUMMARY
        )

    def dump(self, filename=None, outdir=None):
        """Write array constraint metrics to a file or stdout."""

        util.dump(self, filename, outdir)

    def render_report(self, filename=None, outdir=None):
        """Write the array constraint summary to a file rendered as html."""

        array_html = templates.render_array_constraint_summary(self.summary)
        util.dump(array_html, filename or "array.html", outdir)

################################################################
# Json key tags to access elements in cbmc json output

JSON_ARRAY_CONSTRAINTS_KEY = 'arrayConstraints'

# Example cbmc json output
# [
#   {
#     "program": "CBMC 5.13.0 (cbmc-5.13.1-44-g31340ca28-dirty)"
#   },
#   ...
#   {
#     "arrayConstraints": {
#       "arrayAckermann": 5,
#       "arrayEquality": 6,
#       "arrayWith": 8
#     },
#     "numOfConstraints": 19
#   },
#   ...
#   {
#     "arrayConstraints": {
#       "arrayAckermann": 5,
#       "arrayEquality": 6,
#       "arrayWith": 8
#     },
#     "numOfConstraints": 19
#   },
#   ...
#   {
#     "cProverStatus": "..."
#   }
# ]

################################################################
# Utility functions to generate array constraint summary

def get_array_constraint_metrics(json_file):
    summary = {
        'arrayConstraints': {},
        'numOfConstraints': 0
    }

    json_data = parse.parse_json_file(json_file)
    for item in json_data:
        if JSON_ARRAY_CONSTRAINTS_KEY in item.keys():
            if not summary:
                summary.update(item)
                continue

            constraints = item[JSON_ARRAY_CONSTRAINTS_KEY]
            for key in constraints:
                summary['arrayConstraints'][key] = \
                    summary['arrayConstraints'].get(key, 0) + constraints[key]
            summary['numOfConstraints'] += item['numOfConstraints']

    return summary

def fail(msg):
    """Log failure and raise exception."""

    logging.info(msg)
    raise UserWarning(msg)

def do_make_array(cbmc_array_constraint):
    if cbmc_array_constraint:
        if filet.is_json_file(cbmc_array_constraint):
            return ArrayConstraintSummary(cbmc_array_constraint)
        fail("Expected json file: {}"
             .format(cbmc_array_constraint))
