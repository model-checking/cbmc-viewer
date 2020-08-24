# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Trace annotated with debugging information."""

import html
import logging
import os
import re

import voluptuous
import voluptuous.humanize

from cbmc_viewer import markup_link
from cbmc_viewer import srcloct
from cbmc_viewer import templates
from cbmc_viewer import util

# Name of directory holding annotated traces
TRACES = "traces"

################################################################
# Data passed to jinja to generate annotated traces from trace.jinja.html

VALID_STEP = voluptuous.schema_builder.Schema({
    'kind': voluptuous.validators.Any(
        'function-call',
        'function-return',
        'variable-assignment',
        'parameter-assignment',
        'assumption',
        'failure'
    ),
    'num': int,
    'srcloc': str,
    'code': voluptuous.validators.Any(str, None),
    'cbmc': str
}, required=True)

VALID_TRACE = voluptuous.schema_builder.Schema({
    'prop_name': str,
    'prop_desc': str,
    'prop_srcloc': str,
    'steps': [VALID_STEP],
    'outdir': str
}, required=True)

################################################################
# Source code fragments used to annotate traces.

class CodeSnippet:
    """Source code fragments."""

    def __init__(self, root):
        self.root = root  # source root
        self.source = {}  # cache mapping file name -> lines of source code

    def lookup(self, path, line):
        """A line of source code."""

        if line <= 0: # line numbers are 1-based
            logging.info("CodeSnippet lookup: line number not positive: %s", line)
            return None
        line -= 1    # list indices are 0-based

        try:
            if path not in self.source:
                with open(os.path.join(self.root, path)) as code:
                    self.source[path] = code.read().splitlines()
        except FileNotFoundError:
            if srcloct.is_builtin(path): # <builtin-library-malloc>, etc.
                return None
            raise UserWarning(
                "CodeSnippet lookup: file not found: {}".format(path)
            )

        # return the whole statement which may be broken over several lines
        snippet = ' '.join(self.source[path][line:line+5])
        snippet = re.sub(r'\s+', ' ', snippet).strip()
        idx = snippet.find(';')     # end of statement
        if idx >= 0:
            return html.escape(snippet[:idx+1])
        idx = snippet.find('}')     # end of block
        if idx >= 0:
            return html.escape(snippet[:idx+1])
        return html.escape(snippet) # statement extends over more that 5 lines


    def lookup_srcloc(self, srcloc):
        """A line of source code (at a source location)."""

        return self.lookup(srcloc['file'], srcloc['line'])

################################################################

class Trace:
    """Trace annotated with debugging information."""

    def __init__(self, name, trace, symbols, properties, loops, snippets,
                 outdir='.'):
        self.prop_name = name
        self.prop_desc = properties.get_description(name)
        self.prop_srcloc = format_srcloc(properties.get_srcloc(name)
                                         or loops.lookup_assertion(name),
                                         symbols)
        self.steps = [{
            'kind': step['kind'],
            'num': num+1, # convert 0-based index to 1-based line number
            'srcloc': format_srcloc(step['location'], symbols),
            'code': snippets.lookup_srcloc(step['location']),
            'cbmc': format_step(step)
        } for num, step in enumerate(trace)]
        self.outdir = outdir
        self.validate()

    def __str__(self):
        """Render annotated trace as html."""

        return templates.render_trace(self.prop_name,
                                      self.prop_desc,
                                      self.prop_srcloc,
                                      self.steps)

    def validate(self):
        """Validate members of an annotated trace object."""

        return voluptuous.humanize.validate_with_humanized_errors(
            self.__dict__, VALID_TRACE
        )

    def dump(self, filename=None, outdir=None):
        """Write annotated trace to a file rendered as html."""

        util.dump(self,
                  filename or self.prop_name + ".html",
                  outdir or self.outdir)

################################################################
# Format a source location

def format_srcloc(srcloc, symbols):
    """Format a source location for a trace step."""

    if srcloc is None:
        return 'Function none, File none, Line none'

    fyle, func, line = srcloc['file'], srcloc['function'], srcloc['line']
    func_srcloc = symbols.lookup(func)
    # Warning: next line assumes trace root is subdirectory of code root
    from_file = os.path.join(TRACES, 'foo.html') # any name foo.html will do
    return 'Function {}, File {}, Line {}'.format(
        markup_link.link_text_to_srcloc(func, func_srcloc, from_file),
        markup_link.link_text_to_file(fyle, fyle, from_file),
        markup_link.link_text_to_line(line, fyle, line, from_file)
    )

################################################################
# Format a trace step

def format_step(step):
    """Format a trace step."""

    markup = {
        "function-call": format_function_call,
        "function-return": format_function_return,
        "variable-assignment": format_variable_assignment,
        "parameter-assignment": format_parameter_assignment,
        "assumption": format_assumption,
        "failure": format_failure
    }[step['kind']]
    return markup(step)

def format_function_call(step):
    """Format a function call."""

    name, srcloc = step['detail']['name'], step['detail']['location']

    line = '-> {}'.format(
        markup_link.link_text_to_srcloc(name, srcloc, './trace/trace.html')
    )
    return line

def format_function_return(step):
    """Format a function return."""

    name, srcloc = step['detail']['name'], step['detail']['location']
    line = '<- {}'.format(
        markup_link.link_text_to_srcloc(name, srcloc, './trace/trace.html')
    )
    return line

def format_variable_assignment(step):
    """Format an assignment statement."""

    asn = step['detail']
    lhs, rhs, binary = asn['lhs'], asn['rhs-value'], asn['rhs-binary']
    binary = '({})'.format(binary) if binary else ''
    return '{} = {} {}'.format(lhs, rhs, binary)

def format_parameter_assignment(step):
    """Format an assignment of an actual to formal function argument."""

    asn = step['detail']
    lhs, rhs, binary = asn['lhs'], asn['rhs-value'], asn['rhs-binary']
    binary = '({})'.format(binary) if binary else ''
    return '{} = {} {}'.format(lhs, rhs, binary)

def format_assumption(step):
    """Format a proof assumption."""

    pred = step['detail']['predicate']
    return 'assumption: {}'.format(pred)

def format_failure(step):
    """Format a proof failure."""

    prop = step['detail']['property'] or "Unnamed"
    reason = step['detail']['reason'] or "Not given"
    return 'failure: {}: {}'.format(prop, reason)

################################################################
