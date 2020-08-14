# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Links to source code.

This module is a set of methods for constructing links into the
annotated source code.  All other modules use these methods for
consistent links to source code.  All paths in this module are
assumed to be relative to the root of the source code.

"""

import html
import os
import re

from cbmc_viewer import srcloct

################################################################

def path_to_file(dst, src):
    """The path from src to dst for use in a hyperlink from src to dst.

    Given two paths src and dst relative to a common root, return the
    relative path from src to dst.  This is the path to use in a
    hyperlink from src to dst.  For example,
    the path from 'a/b/foo.html' to 'c/bar.html' is '../../c/bar.html',
    the path from 'a/b/foo.html' to '.' is '../..', and
    the path from '.' to 'a/b/foo.html' is 'a/b/foo.html'.
    """

    path = os.path.relpath(dst, os.path.dirname(src))
    assert dst == os.path.normpath(os.path.join(os.path.dirname(src), path))
    return path

################################################################
# Method to link into the source tree.
# By default, links are from the root of the source tree to the source file.

def link_text_to_file(text, to_file, from_file=None):
    """Link text to a file in the source tree."""

    if srcloct.is_builtin(to_file):
        return html.escape(str(text))

    from_file = from_file or '.'
    path = path_to_file(to_file, from_file)
    return '<a href="{}.html">{}</a>'.format(path, text)

def link_text_to_line(text, to_file, line, from_file=None):
    """Link text to a line in a file in the source tree."""

    if srcloct.is_builtin(to_file):
        return html.escape(str(text))

    from_file = from_file or '.'
    line = int(line)
    path = path_to_file(to_file, from_file)
    return '<a href="{}.html#{}">{}</a>'.format(path, line, text)

def link_text_to_srcloc(text, srcloc, from_file=None):
    """Link text to a source location in a file in the source tree."""

    if srcloc is None:
        return text
    return link_text_to_line(text, srcloc['file'], srcloc['line'], from_file)

def link_text_to_symbol(text, symbol, symbols, from_file=None):
    """Link text to a symbol definition in the source tree."""

    srcloc = symbols.lookup(symbol)
    return link_text_to_srcloc(text, srcloc, from_file)

def split_text_into_symbols(text):
    """Split text into substrings that could be symbols."""

    return re.split('([_a-zA-Z][_a-zA-Z0-9]*)', text)

def link_symbols_in_text(text, symbols, from_file=None):
    """Link symbols appearing in text to their definitions."""

    if text is None:
        return None

    tokens = split_text_into_symbols(text)
    return ''.join(
        [link_text_to_symbol(tkn, tkn, symbols, from_file)
         for tkn in tokens]
    )

################################################################
