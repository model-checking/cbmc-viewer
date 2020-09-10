# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Jinja templates."""

import jinja2

import pkg_resources

PACKAGE = 'cbmc_viewer'
TEMPLATES = 'templates'

SUMMARY_TEMPLATE = 'summary.jinja.html'
CODE_TEMPLATE = 'code.jinja.html'
TRACE_TEMPLATE = 'trace.jinja.html'

# runtime analysis metrics
CLAUSE_SUMMARY_TEMPLATE = 'clause.jinja.html'

ENV = None

def env():
    """The jinja environment."""

    # pylint: disable=global-statement
    global ENV

    if ENV is None:
        template_dir = pkg_resources.resource_filename(PACKAGE, TEMPLATES)
        ENV = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir)
        )
    return ENV

def render_summary(summary):
    """Render summary as html."""

    return env().get_template(SUMMARY_TEMPLATE).render(
        summary=summary
    )

def render_code(filename, path_to_root, lines):
    """Render annotated source code as html."""

    return env().get_template(CODE_TEMPLATE).render(
        filename=filename, path_to_root=path_to_root, lines=lines
    )

def render_trace(name, desc, srcloc, steps):
    """Render annotated trace as html."""

    return env().get_template(TRACE_TEMPLATE).render(
        prop_name=name, prop_desc=desc, prop_srcloc=srcloc, steps=steps
    )

def render_clause_summary(clause_summary, core_instr, loc_not_in_core):
    """Render solver query complexity metric as html."""

    return env().get_template(CLAUSE_SUMMARY_TEMPLATE).render(
        summary=clause_summary, core=core_instr, notcore=loc_not_in_core
    )
