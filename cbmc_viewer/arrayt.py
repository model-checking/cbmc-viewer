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

import voluptuous
import voluptuous.humanize

from cbmc_viewer import filet
from cbmc_viewer import parse
from cbmc_viewer import templates
from cbmc_viewer import util

################################################################

VALID_CONSTRAINT = voluptuous.schema_builder.Schema({
    str: int # example: arrayWith, arrayAckermann
    })

VALID_ARRAY_CONSTRAINTS = voluptuous.schema_builder.Schema({
    'arrayConstraints': VALID_CONSTRAINT,
    'numOfConstraints': int
    },required=True)

VALID_SUMMARY = voluptuous.schema_builder.Schema({
    'summary': VALID_ARRAY_CONSTRAINTS
    },required=True)

################################################################

class ArrayConstraintSummary:

    def __init__(self, json_file):
        self.summary = do_make_array_constraint(json_file)
        self.validate()

    def __str__(self):
        """Render the array constraint summary as html."""
        return templates.render_array_constraint_summary(self.summary)

    def validate(self):
        """Validate members of a summary object."""

        return voluptuous.humanize.validate_with_humanized_errors(
            self.__dict__, VALID_SUMMARY
        )

    def dump(self, filename=None, outdir='.'):
        """Write the array constraint summary to a file rendered as html."""

        util.dump(self, filename or "array.html", outdir)

################################################################
# Json key tags to access elements in cbmc json output

JSON_ARRAY_CONSTRAINTS_KEY = 'arrayConstraints'

################################################################
# Utility functions to generate array constraint summary

def get_array_constraint_metrics(json_file):
    summary = {}

    json_data = parse.parse_json_file(json_file)
    for item in json_data:
        if JSON_ARRAY_CONSTRAINTS_KEY in item.keys():
            array_constraints_item = item
            summary.update(array_constraints_item)
            break

    if not summary:
        summary = {
            'arrayConstraints': {},
            'numOfConstraints': 0
        }

    return summary

def fail(msg):
    """Log failure and raise exception."""

    logging.info(msg)
    raise UserWarning(msg)

def do_make_array_constraint(cbmc_array_constraint):
    if cbmc_array_constraint:
        if filet.is_json_file(cbmc_array_constraint):
            return get_array_constraint_metrics(cbmc_array_constraint)
        fail("Expected json file: {}"
             .format(cbmc_array_constraint))
