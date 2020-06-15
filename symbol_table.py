# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Symbol table parser for a goto binary symbol table."""

import logging
import os
import re

import srcloct
import runt

def symbol_table(goto):
    """Extract symbol table from goto binary as lines of text."""

    cmd = ['cbmc', '--show-symbol-table', goto]
    return runt.run(cmd).splitlines()

def is_symbol_line(line):
    """Line is a symbol table symbol definition line."""

    return line.startswith('Symbol.') # Match Symbol. not Symbols:

def is_location_line(line):
    """Line is a symbol table symbol location line."""

    return line.startswith('Location')

def parse_symbol(sym):
    """Symbol definition from symbol definition line."""

    if not is_symbol_line(sym):
        return None

    match = re.match('.*: (tag-)?([a-zA-Z0-9_]*$)', sym)
    if match is None:
        return None

    return match.group(2)

def parse_location(loc, wkdir):
    """Symbol source location from symbol location line."""

    if not is_location_line(loc):
        return None, None

    match = re.match('.* file (.*) line ([0-9]*)', loc)
    if match is None:
        return None, None

    rel_path, line = match.group(1), int(match.group(2))
    abs_path = srcloct.normpath(os.path.join(wkdir, rel_path))
    if srcloct.is_builtin(abs_path):
        return None, None

    return abs_path, line

def source_files(goto, wkdir, srcdir=None):
    """Source files appearing in symbol table.

    Source file path names in symbol table are absolute or relative to
    wkdir.  If srcdir is given, return only files under srcdir.
    """

    wkdir = srcloct.abspath(wkdir)
    srcdir = srcloct.abspath(srcdir) if srcdir is not None else None

    loc_lines = [line for line in symbol_table(goto) if is_location_line(line)]
    locs = [parse_location(loc_line, wkdir) for loc_line in loc_lines]
    paths = [path for path, _ in locs if path is not None]

    srcs = [path for path in paths if not srcloct.is_builtin(path)]
    if srcdir is not None:
        srcs = [path for path in srcs if path.startswith(srcdir)]

    return sorted(set(srcs))

def symbol_definitions(goto, wkdir, srcdir=None):
    """Symbol definitions appearing in symbol table.

    Source file path names in symbol table are absolute or relative to
    wkdir.  If srcdir is given, return only symbols defined in files
    under srcdir.
    """

    wkdir = srcloct.abspath(wkdir)
    srcdir = srcloct.abspath(srcdir) if srcdir is not None else None

    lines = [line for line in symbol_table(goto)
             if is_symbol_line(line) or is_location_line(line)]

    syms = {}
    while lines:
        try:
            sym_line, loc_line = lines[0:2]
            lines = lines[2:]
        except ValueError:
            raise UserWarning('Symbol table ended with umatched line: "{}"'
                              .format(lines))

        if not is_symbol_line(sym_line) or not is_location_line(loc_line):
            raise UserWarning('Symbol table included unmatched lines: '
                              '"{}" and "{}"'
                              .format(sym_line, loc_line))

        sym = parse_symbol(sym_line)
        path, line = parse_location(loc_line, wkdir)
        if sym is None or path is None or line is None:
            continue
        if srcdir is not None and not path.startswith(srcdir):
            continue
        sym_srcloc = srcloct.make_srcloc(path, None, line, wkdir, srcdir)
        if sym in syms and sym_srcloc != syms[sym]:
            logging.warning("Skipping redefinition of symbol name: %s", sym)
            logging.warning("  Old symbol %s: file %s, line %s",
                            sym, syms[sym]["file"], syms[sym]["line"])
            logging.warning("  New symbol %s: file %s, line %s",
                            sym, sym_srcloc["file"], sym_srcloc["line"])
            continue
        syms[sym] = sym_srcloc

    return syms
