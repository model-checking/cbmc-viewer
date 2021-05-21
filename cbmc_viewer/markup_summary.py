# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Proof summary."""

import voluptuous
import voluptuous.humanize

from cbmc_viewer import templates
from cbmc_viewer import util

################################################################
# Data passed to jinja to generate proof summary from summary.jinja.html

VALID_SUMMARY_DATA = voluptuous.schema_builder.Schema({
    # coverage section of the summary
    'coverage': {
        'overall': {
            'percentage': float, # percentage of lines hit
            'hit': int, # lines hit
            'total': int # lines total
        },
        'function': [{
            'percentage': float, # percentage of lines hit
            'hit': int, # lines hit
            'total': int, # lines total
            'file_name': str,
            'func_name': str,
            'line_num': int,

        }]
    },
    # warning section of the summary
    'warnings': {
        'expected_missing_function': [str], # function names
        'unexpected_missing_function': [str], # function names
        'other': [str] # warning messages
    },
    # failure sections of the summary
    'failures': {
        'property': [{ # assertion failures
            'prop_name': str,
            'prop_desc': str,
            'file_name': str,
            'func_name': str,
            'line_num': int,
            'func_line': int
        }],
        'loop': [{ # loop unwinding assertion failures
            'loop_name': str,
            'file_name': str,
            'func_name': str,
            'line_num': int
        }],
        'other': [str] # unrecognized failure names
    }
}, required=True)

VALID_SUMMARY = voluptuous.schema_builder.Schema({
    'summary': VALID_SUMMARY_DATA,
    'outdir': str # default output directory for dump()
}, required=True)

################################################################

class Summary:
    """Proof summary.

    The summary merges results produced by cbmc into a single report.
    """

    def __init__(self, coverage, symbols, results, properties, loops,
                 config, outdir='.'):
        # pylint: disable=too-many-arguments

        self.summary = {
            'coverage': {
                'overall': overall_coverage(coverage),
                'function': function_coverage(coverage, symbols)
            },
            'warnings': {
                'expected_missing_function':
                    expected_missing_functions(results, config),
                'unexpected_missing_function':
                    unexpected_missing_functions(results, config),
                'other': other_warnings(results)
            },
            'failures': {
                'property': property_failures(results, properties, symbols),
                'loop': loop_failures(results, loops),
                'other': other_failures(results, properties, loops)
            }
        }
        self.outdir = outdir
        self.validate()

    def __str__(self):
        """Render the proof summary as html."""

        return templates.render_summary(self.summary)

    def validate(self):
        """Validate members of a summary object."""

        return voluptuous.humanize.validate_with_humanized_errors(
            self.__dict__, VALID_SUMMARY
        )

    def dump(self, filename=None, outdir=None):
        """Write the proof summary to a file rendered as html."""

        util.dump(self, filename or "index.html", outdir or self.outdir)

################################################################
# Coverage data

def overall_coverage(coverage):
    """Overall proof coverage."""

    cov = coverage.overall_coverage
    return {
        'percentage': cov['percentage'],
        'hit': cov['hit'],
        'total': cov['total']
    }

def function_coverage(coverage, symbols):
    """Function proof coverage."""

    return [
        {
            'percentage': func_cov['percentage'],
            'hit': func_cov['hit'],
            'total': func_cov['total'],
            'file_name': file_name,
            'func_name': func_name,
            'line_num': symbols.lookup(func_name).get("line") if symbols.lookup(func_name) else 0
        }
        for file_name, file_data in coverage.function_coverage.items()
        for func_name, func_cov in file_data.items()
    ]

################################################################
# Warning data

# TODO: This classification of warnings should be done by make-results

def warnings(results):
    """Proof warnings."""

    prefixes = ["**** WARNING:", "warning:"]

    def strip_prefixes(string, prefixes):
        """Strip warning prefixes from a warning string."""

        for prefix in prefixes:
            if string.startswith(prefix):
                return string[len(prefix):].strip()
        return string

    return [strip_prefixes(warning, prefixes) for warning in results.warning]

def missing_functions(messages):
    """Names of missing functions."""

    prefix = "no body for function"
    length = len(prefix)
    return [warning[length:].strip() for warning in messages
            if warning.startswith(prefix)]

def expected_missing_functions(results, config):
    """Names of missing functions expected to be missing."""

    return [
        function for function in missing_functions(warnings(results))
        if function in config.expected_missing_functions()
    ]

def unexpected_missing_functions(results, config):
    """Names of missing functions not expected to be missing."""

    return [
        function for function in missing_functions(warnings(results))
        if function not in config.expected_missing_functions()
    ]

def other_warnings(results):
    """Warnings unrelated to missing functions."""

    prefix = "no body for function"
    return [warning.strip() for warning in warnings(results)
            if not warning.startswith(prefix)]

################################################################
# Failure data

def property_definition(prop_name, properties, symbols):
    """Details for a property failure."""

    prop_def = properties.lookup(prop_name)
    if prop_def is None:
        return None

    srcloc = prop_def['location']
    return {
        'prop_name': prop_name,
        'prop_desc': prop_def['description'],
        'file_name': srcloc['file'],
        'func_name': srcloc['function'] or '',
        'line_num': srcloc['line'],
        'func_line':
            # Symbol table won't contain functions modeled by CBMC (eg, strcmp)
            # Return a line number 0 for such functions
            (symbols.lookup(srcloc['function']) or {'line': 0})['line']
    }

def loop_definition(prop_name, loops):
    """Details for a loop unwinding assertion failure."""

    srcloc = loops.lookup_assertion(prop_name)
    if srcloc is None:
        return None

    return {
        'loop_name': prop_name,
        'file_name': srcloc['file'],
        'func_name': srcloc['function'],
        'line_num': srcloc['line']
    }

def other_definition(prop_name, properties, loops):
    """Name of an unrecognized failure."""

    if properties.lookup(prop_name) or loops.lookup_assertion(prop_name):
        return None
    return prop_name

def filter_none(items):
    """Remove instances of None from a list of items."""

    return [item for item in items if item is not None]

def property_failures(results, properties, symbols):
    """Details for property failures."""

    failures = results.results[False]
    return filter_none(
        [property_definition(failure, properties, symbols)
         for failure in failures]
    )

def loop_failures(results, loops):
    """Details for loop unwinding assertion failures."""

    failures = results.results[False]
    return filter_none(
        [loop_definition(failure, loops) for failure in failures]
    )

def other_failures(results, properties, loops):
    """Names of unrecognized failures."""

    failures = results.results[False]
    return filter_none(
        [other_definition(failure, properties, loops) for failure in failures]
    )

################################################################
