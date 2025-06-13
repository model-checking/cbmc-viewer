# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Jinja templates."""

import jinja2
from jinja2 import select_autoescape

from importlib import resources as importlib_resources

PACKAGE = 'cbmc_viewer'
TEMPLATES = 'templates'

SUMMARY_TEMPLATE = 'summary.jinja.html'
CODE_TEMPLATE = 'code.jinja.html'
TRACE_TEMPLATE = 'trace.jinja.html'

ENV = None

def env():
    """The jinja environment."""

    # pylint: disable=global-statement
    global ENV

    if ENV is None:
        try:
            ctxmgr = importlib_resources.as_file(
                        importlib_resources.files(PACKAGE) / TEMPLATES)
        except AttributeError:
            # Python 3.7 and 3.8
            ctxmgr = importlib_resources.path(PACKAGE, TEMPLATES)
        with ctxmgr as templates_path:
            ENV = jinja2.Environment(
                loader=jinja2.FileSystemLoader(str(templates_path)),
                autoescape=select_autoescape(
                    enabled_extensions=('html'),
                    default_for_string=True)
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
