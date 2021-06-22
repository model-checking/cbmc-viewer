# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Symbol table parser for a goto binary symbol table."""

import logging
import os
import re

from cbmc_viewer import runt
from cbmc_viewer import srcloct
from cbmc_viewer.source_language import Language

def symbol_table(goto):
    """Extract symbol table from goto binary as lines of text."""

    # The --show-symbol-table flag produces a sequence of symbol
    # definitions.  Definitions are separated by blank lines.  Each
    # definition is a sequence of lines including
    #
    #   Symbol......: symbol_name
    #   Pretty name.: simple_symbol_name
    #   Location....: file file_name line line_number

    # Code with definitions like
    #   static const char *UTF_16_BE_BOM = "\xFE\xFF";
    # will produce values in the symbol table that cannot be read as
    # strings of UTF-8 characters.  We read the symbol table using the
    # latin1 encoding in place of the Python default UTF-8 encoding,
    # since latin1 agrees with UTF-8 on the ASCII characters.

    cmd = ['cbmc', '--show-symbol-table', goto]
    definitions = re.split(r'[\n\r][\n\r]+', runt.run(cmd, encoding='latin1'))
    return [definition.strip().splitlines() for definition in definitions]

def is_symbol_line(line):
    """Line from symbol table defines a symbol name."""

    return line.startswith('Symbol.') # Match Symbol. not Symbols:

def is_location_line(line):
    """Line from symbol table defines a location of a symbol definition."""

    return line.startswith('Location')

def is_pretty_name_line(line):
    """Line from symbol table defines a simple symbol name (a pretty name)."""

    return line.startswith('Pretty name')

def parse_symbol(sym):
    """Symbol name from symbol line."""

    if not is_symbol_line(sym):
        return None

    # Examples of symbol lines
    # Symbol......: function_name
    # Symbol......: function_name$link1
    # Symbol......: function_name::parameter_name
    # Symbol......: function_name::1::1::variable_name
    # Symbol......: tag-struct_name
    # Symbol......: tag-union_name

    name = sym.split(":", 1)[1].strip()
    return Language.match_symbol(name)

def parse_location(loc, wkdir):
    """Symbol source location from location line."""

    if not is_location_line(loc):
        return None, None

    # Examples of location lines (may be no location for symbol)
    # Location....:
    # Location....: file file_name line line_number

    match = re.match('.* file (.*) line ([0-9]*)', loc)
    if match is None:
        return None, None

    rel_path, line = match.group(1), int(match.group(2))
    abs_path = srcloct.normpath(os.path.join(wkdir, rel_path))
    if srcloct.is_builtin(abs_path):
        return None, None

    return abs_path, line

def parse_pretty_name(sym):
    """Symbols pretty name from pretty name line."""

    if not is_pretty_name_line(sym):
        return None

    # Examples of pretty name lines (may be no pretty name for symbol)
    # Pretty name.:
    # Pretty name.: function_name
    # Pretty name.: function_name::1::1::variable_name
    # Pretty name.: struct struct_name
    # Pretty name.: union union_name

    name = sym.split(":", 1)[1].strip()
    return Language.match_pretty_name(name)

def parse_symbol_table(definitions, wkdir):
    """Extract symbols and source locations from symbol table definitions."""

    def nonnull(items):
        nonnull_items = [item for item in items if item is not None]
        if nonnull_items:
            return nonnull_items[0]
        return None

    def nonnull_pair(items):
        nonnull_items = [item for item in items if item is not None
                         and (item[0] is not None or item[1] is not None)]
        if nonnull_items:
            return nonnull_items[0]
        return None, None

    def symbol(dfn):
        return nonnull([parse_symbol(line) for line in dfn])

    def pretty(dfn):
        return nonnull([parse_pretty_name(line) for line in dfn])

    def location(dfn, wkdir):
        return nonnull_pair([parse_location(line, wkdir) for line in dfn])

    def parse_definition(dfn, wkdir):
        loc = location(dfn, wkdir)
        return {
            'symbol': pretty(dfn) or symbol(dfn),
            'file': loc[0],
            'line': loc[1]
        }

    return [parse_definition(dfn, wkdir) for dfn in definitions]

def source_files(goto, wkdir, srcdir=None):
    """Source files appearing in symbol table.

    Source file path names in symbol table are absolute or relative to
    wkdir.  If srcdir is given, return only files under srcdir.
    """

    wkdir = srcloct.abspath(wkdir)
    srcs = [dfn['file']
            for dfn in parse_symbol_table(symbol_table(goto), wkdir)]
    srcs = [src for src in srcs if src and not srcloct.is_builtin(src)]

    if srcdir:
        srcdir = srcloct.abspath(srcdir)
        srcs = [src for src in srcs if src.startswith(srcdir)]

    return sorted(set(srcs))

def symbol_definitions(goto, wkdir, srcdir=None):
    """Symbol definitions appearing in symbol table.

    Source file path names in symbol table are absolute or relative to
    wkdir.  If srcdir is given, return only symbols defined in files
    under srcdir.
    """

    wkdir = srcloct.abspath(wkdir)
    srcdir = srcloct.abspath(srcdir)

    symbols = {}
    for dfn in parse_symbol_table(symbol_table(goto), wkdir):
        sym, src, num = dfn['symbol'], dfn['file'], dfn['line']

        if sym is None or src is None or num is None:
            logging.info("Skipping symbol table entry: %s: %s, %s",
                         sym, src, num)
            continue

        if srcdir and not src.startswith(srcdir):
            logging.info("Skipping symbol table entry: %s: %s, %s",
                         sym, src, num)
            continue

        srcloc = srcloct.make_srcloc(src, None, num, wkdir, srcdir)
        if sym in symbols and srcloc != symbols[sym]:
            logging.warning("Skipping redefinition of symbol name: %s", sym)
            logging.warning("  Old symbol %s: file %s, line %s",
                            sym, symbols[sym]["file"], symbols[sym]["line"])
            logging.warning("  New symbol %s: file %s, line %s",
                            sym, srcloc["file"], srcloc["line"])
            continue
        symbols[sym] = srcloc

    return symbols
