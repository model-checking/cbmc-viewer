# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Annotated source code."""

import html
import logging
import os
import re

import voluptuous
import voluptuous.humanize

from cbmc_viewer import markup_link
from cbmc_viewer import templates
from cbmc_viewer import util

################################################################
# Data passed to jinja to generate annotated code from code.jinja.html

VALID_LINE = voluptuous.Schema({
    'num': int,
    'status': voluptuous.Any('hit', 'missed', 'both', 'none'),
    'code': str,
}, required=True)

VALID_CODE = voluptuous.Schema({
    'filename': str,
    'path_to_root': str,
    'lines': [VALID_LINE],
    'outdir': str
}, required=True)

################################################################
# An annotated file of source code.

class Code:
    """An annotated file of source code."""

    def __init__(self, root, path, symbols, coverage, outdir='.'):

        try:
            # load code into a string
            with open(os.path.join(root, path)) as source:
                code = html.escape(untabify_code(source.read()), quote=False)

            # split code into blocks of code, comments, and string literals
            blocks = split_code_into_blocks(code)

            # link symbols in code blocks to symbol definitions
            linked_blocks = link_symbols_in_code_blocks(path, blocks, symbols)

            # reform code as a string with symbols linked to definitions
            linked_code = ''.join(linked_blocks)

            # break code into lines annotated with line number and line coverage
            annotated_lines = annotate_code(path, linked_code, coverage)

            self.lines = annotated_lines
        except FileNotFoundError:
            # The goto symbol table occassional refers to header files
            # like gcc_builtin_headers_types.h that are part of the
            # CBMC implementation.
            #   * We skip source annotation: We treat the file as a
            #     zero-length file with nothing to annotate.
            #   * We print a simple warning message: The relative path
            #     to the file in the symbol table was interpreted by
            #     the symbol table parser as relative to the working
            #     directory.  Printing this path in the warning is
            #     confusing, so we print just the base name.
            logging.warning("Skipping source file annotation: %s",
                            os.path.basename(path))
            self.lines = []

        self.filename = path
        self.path_to_root = markup_link.path_to_file('.', path)
        self.outdir = outdir
        self.validate()

    def __str__(self):
        """Render annotated code as html."""

        return templates.render_code(self.filename,
                                     self.path_to_root,
                                     self.lines)

    def validate(self):
        """Validate members of a code object."""

        return voluptuous.humanize.validate_with_humanized_errors(
            self.__dict__, VALID_CODE
        )

    def dump(self, filename=None, outdir=None):
        """Write annotated code to a file rendered as html."""

        util.dump(self,
                  filename or self.filename + ".html",
                  outdir or self.outdir)

################################################################
# Untabify code: replace tabs with spaces.

def untabify_code(code, tabstop=8):
    """Untabify a block of code."""

    return '\n'.join(
        [untabify_line(line, tabstop) for line in code.splitlines()]
    )

def untabify_line(line, tabstop=8):
    """Untabify a line of code."""

    strings = []
    length = 0
    for string in re.split('(\t)', line):
        if string == '\t':
            string = ' '*(tabstop - (length % tabstop))
        length += len(string)
        strings.append(string)
    return ''.join(strings)

################################################################
# Split code into code blocks and strings/comments

def split_code_into_blocks(code):
    """Split code into blocks of code, comments, and string literals."""

    def is_noncode_start(code, idx=0):
        """String starts something other than source code (eg, a comment)."""

        return (is_quote(code, idx) or
                is_multiline_comment_start(code, idx) or
                is_singleline_comment_start(code, idx))

    def find_predicate(code, predicate, idx=0):
        """First position in a string satisfying a predicate."""

        while idx < len(code) and not predicate(code, idx):
            idx += 1
        return idx

    blocks = []

    while code:
        idx = find_predicate(code, is_noncode_start)
        block, code, idx = code[:idx], code[idx:], 0
        if block:
            blocks.append(block)

        if not code:
            break

        if is_quote(code):
            idx = find_predicate(code, is_quote, 1)
        elif is_multiline_comment_start(code):
            idx = find_predicate(code, is_multiline_comment_end, 2)
        elif is_singleline_comment_start(code):
            idx = find_predicate(code, is_singleline_comment_end, 2)
        block, code, idx = code[:idx+1], code[idx+1:], 0
        if block:
            blocks.append(block)

    return blocks

def is_quote(code, idx=0):
    """Position in string is an unescaped quotation mark."""
    return (0 <= idx < len(code) and
            code[idx] == '"' and
            (idx == 0 or code[idx-1] != '\\'))

def is_multiline_comment_start(code, idx=0):
    """Position in string starts a multi-line comment."""
    return idx >= 0 and idx+2 <= len(code) and code[idx:idx+2] == '/*'

def is_multiline_comment_end(code, idx=0):
    """Position in string ends a multi-line comment."""
    return idx-1 >= 0 and idx+1 <= len(code) and code[idx-1:idx+1] == '*/'

def is_singleline_comment_start(code, idx=0):
    """Position in string starts a one-line comment."""
    return idx >= 0 and idx+2 <= len(code) and code[idx:idx+2] == '//'

def is_singleline_comment_end(code, idx=0):
    """Position in string ends a one-line comment."""
    return idx >= 0 and idx+1 < len(code) and code[idx+1] == '\n'

################################################################
# Link symbols in code blocks

def link_symbols_in_code_blocks(path, blocks, symbols):
    """Link symbols appearing a sequence of blocks."""

    return [link_symbols_in_code_block(path, block, symbols)
            for block in blocks]

def link_symbols_in_code_block(path, block, symbols):
    """Link symbols appearing a code block."""

    if (is_quote(block) or
            is_multiline_comment_start(block) or
            is_singleline_comment_start(block)):
        return block

    return link_symbols(path, block, symbols)

def link_symbols(path, code, symbols):
    """Link symbols appearing a code string."""

    tokens = split_code_into_symbols(code)
    return ''.join(
        [markup_link.link_text_to_symbol(tkn, tkn, symbols, from_file=path, escape_text=False)
         for tkn in tokens]
    )

def split_code_into_symbols(code):
    """Split a code string into a list of symbols and nonsymbols."""

    return re.split('([_a-zA-Z][_a-zA-Z0-9]*)', code)

################################################################
# Annotate lines of symbol-linked code with line numbers and coverage

def annotate_code(path, code, coverage):
    """Annotate lines of code with line numbers and coverage status."""

    return [{ # line_num is 0-based, line numbers are 1-based
        'num': line_num+1,
        'status': str(coverage.lookup(path, line_num+1)).lower(),
        'code': line
    } for (line_num, line) in enumerate(code.splitlines())]
