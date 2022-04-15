# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""The symbols used to build a goto binary."""

import json
import logging

import voluptuous
import voluptuous.humanize

from cbmc_viewer import parse
from cbmc_viewer import runt
from cbmc_viewer import sourcet
from cbmc_viewer import srcloct
from cbmc_viewer import symbol_table
from cbmc_viewer import util

JSON_TAG = 'viewer-symbol'

################################################################
# Data validator for symbol object

VALID_SYMBOL = voluptuous.Schema({
    'symbols': {
        # symbol name -> symbol srcloc
        voluptuous.Optional(str) : srcloct.VALID_SRCLOC
    }
}, required=True)

################################################################
# Symbol class and subclasses

class Symbol:
    """A mapping from symbols to source locations."""

    def __init__(self, symbols=None):
        """Save and validate a mapping from symbols to source locations."""

        self.symbols = symbols or {}

        # show progress: symbol validation can be slow on large tables
        logging.info('Validating symbol definitions...')
        self.validate()
        logging.info('Validating symbol definitions...done')

    def __repr__(self):
        """A dict representation of a symbol table."""

        # Skip output validation.  It can take 30 seconds on large
        # tables, and the common case is to write the symbol table
        # immediately after building (and validating) the table.
        return self.__dict__

    def __str__(self):
        """A string representation of a symbol table."""

        return json.dumps({JSON_TAG: self.__repr__()},
                          indent=2,
                          sort_keys=True)

    def validate(self):
        """Validate symbols."""

        return voluptuous.humanize.validate_with_humanized_errors(
            self.__dict__, VALID_SYMBOL
        )

    def dump(self, filename=None, directory=None):
        """Write symbols to a file or stdout."""

        util.dump(self, filename, directory)

    def lookup(self, symbol):
        """Look up a symbol's source location."""

        return self.symbols.get(symbol)

################################################################

class SymbolFromJson(Symbol):
    """Load symbol table from the output of make-source.

    Given a list of json files containing symbol tables produced by
    make-symbol, merge these symbol tables into a single symbol table.
    """

    def __init__(self, symbol_jsons):

        if not symbol_jsons:
            raise UserWarning('No symbols')

        def load(symbol_json):
            return parse.parse_json_file(symbol_json)[JSON_TAG]

        def merge(tables):
            return util.merge_dicts(tables)

        super().__init__(
            merge([load(symbol_json) for symbol_json in symbol_jsons])
        )

################################################################

class SymbolFromCtags(Symbol):
    """Create a symbol table with ctags."""

    def __init__(self, root, files):
        """Run ctags on files in the source root."""

        super().__init__(
            parse_ctags_data(run_ctags(root, files), root)
        )

################################################################

class SymbolFromGoto(Symbol):
    """Load symbol table from a goto binary.

    Extract symbols listed in the symbol table of a goto binary.  Use
    ctags to extract symbols from source files listed in the symbol
    table (which will find type definitions and preprocessor
    definitions not appearing in the goto symbol table).  Merge these
    lists of symbol definitions, with definitions in the symbol table
    taking precedence over definitions in the ctags output.  This
    still omits definitions from files that list only definitions and
    do not contribute symbols to the symbol table.
    """

    def __init__(self, goto, wkdir, srcdir):

        def symbols_from_table(goto, wkdir, srcdir):
            """Symbols defined in the symbol table"""

            return symbol_table.symbol_definitions(goto, wkdir, srcdir)

        def symbols_from_files(goto, wkdir, srcdir):
            """Symbols defined in files listed in the symbol table"""

            files = symbol_table.source_files(goto, wkdir, srcdir)
            return SymbolFromCtags(srcdir, files).symbols

        table_symbols = symbols_from_table(goto, wkdir, srcdir)
        file_symbols = symbols_from_files(goto, wkdir, srcdir)

        # symbols from symbol table dominate symbols from ctags
        symbols = file_symbols
        symbols.update(table_symbols)

        super().__init__(symbols)

################################################################
# Parse a ctags file
#
# This is not easy.  The default output of ctags identifies the symbol
# definition with a file name and a vi regular expression to locate
# the symbol within the file.  We use the textual output of ctags that
# gives a file name and a line number, but the textual output is
# intended to be human readable and not machine parsable.

EXUBERANT = 'exuberant'
UNIVERSAL = 'universal'
CTAGS = 'ctags'

def have_ctags():
    """Test for existence of exuberant or universal ctags."""

    try:
        ctags_help = runt.run([CTAGS, '--help']).splitlines()[0]
        ctags_tokens = ctags_help.lower().split()
        return (
            (EXUBERANT in ctags_tokens and CTAGS in ctags_tokens) or
            (UNIVERSAL in ctags_tokens and CTAGS in ctags_tokens)
        )
    except FileNotFoundError:
        return False

def run_ctags(root, files, chunk=2000):
    """Run ctags from the given root over the given files.

    Some operating systems limit the number of command line arguments
    (or the length of the command), we we process the list of files in
    chunks.
    """

    if not files:
        return ''

    logging.info('Running ctags on %s files...', len(files))
    ctags_data = []
    while files:
        paths = files[:chunk]
        files = files[chunk:]
        logging.info('Running ctags on %s files starting with %s...',
                     len(paths), paths[0])
        ctags_output = runt.run(
            [CTAGS, '-n', '-f', '-'] + paths, cwd=root, encoding='latin1'
        )
        ctags_data += ctags_output.splitlines()
    logging.info('Running ctags on %s files...done', len(files))
    return ctags_data

def parse_ctags_data(ctags_data, root):
    """Parse the ctags output into a mapping from symbol to source location."""

    logging.info('Parsing ctag data...')

    symbols = {}
    for line in ctags_data:
        # line has the form: symbol<tab>file<tab>line;" ...

        symbol, filename, linenumber = line.split(';"')[0].split("\t")
        srcloc = srcloct.make_srcloc(
            filename, None, linenumber, root, root
        )

        old_srcloc = symbols.get(symbol)
        if old_srcloc:
            logging.debug(
                'Symbol definition: %s: skipping %s, %s; keeping %s %s',
                symbol,
                srcloc['file'], srcloc['line'],
                old_srcloc['file'], old_srcloc['line']
            )
            continue

        symbols[symbol] = srcloc

    logging.info('Parsing ctag data...done')
    return symbols

################################################################
# make-symbol

# pylint: disable=inconsistent-return-statements

def fail(msg):
    """Log failure and raise exception."""

    logging.info(msg)
    raise UserWarning(msg)

def make_symbol(args):
    """Implementation of make-symbol."""

    viewer_symbol, viewer_source, goto, wkdir, srcdir, files = (
        args.viewer_symbol, args.viewer_source, args.goto, args.wkdir, args.srcdir, args.files)

    wkdir = srcloct.abspath(wkdir) if wkdir else None
    srcdir = srcloct.abspath(srcdir) if srcdir else None

    # Command line options may enable more than one way
    # to generate the symbol table, so choose the one
    # that gives the most "accurate" results.

    if viewer_symbol:
        logging.info("Symbols by SymbolFromJson")
        return SymbolFromJson(viewer_symbol)

    if viewer_source:
        sources = sourcet.SourceFromJson(viewer_source)
        srcdir = sources.root
        files = sources.files

    if srcdir and files:
        SymbolFromCtags(srcdir, files)

    if goto and wkdir and srcdir:
        logging.info("Symbols by SymbolFromGoto")
        return SymbolFromGoto(goto, wkdir, srcdir)

    logging.info("make-symbol: nothing to do: need "
                 "--goto and --wkdir and --srcdir or "
                 "--viewer-source or"
                 "--viewer-symbol")
    return Symbol()

################################################################
