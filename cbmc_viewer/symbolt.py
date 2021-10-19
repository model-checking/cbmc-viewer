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

VALID_SYMBOL = voluptuous.schema_builder.Schema({
    'symbols': {
        # symbol name -> symbol srcloc
        voluptuous.schema_builder.Optional(str) : srcloct.VALID_SRCLOC
    }
}, required=True)

################################################################

class Symbol:
    """The symbols used to build a goto binary."""

    def __init__(self, symbols):

        self.symbols = symbols

        # show progress: symbol validation can be slow on large tables
        logging.info('Validating symbol definitions...')
        self.validate()
        logging.info('Validating symbol definitions...done')

    def lookup(self, symbol):
        """Look up the srcloc for a name in the symbol table."""

        return self.symbols.get(symbol)

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

    @staticmethod
    def build_symbol_table(root, definitions):
        """Build a symbol table using parsed output of ctags."""

        logging.info('Building symbol table from tags data...')
        symbols = {}
        for symbol, filename, linenumber in definitions:
            if symbol in symbols:
                logging.debug('Found duplicate definition: %s: %s, %s <- %s %s',
                              symbol,
                              symbols[symbol]['file'], symbols[symbol]['line'],
                              filename, linenumber)
                continue
            symbols[symbol] = srcloct.make_srcloc(
                filename, None, linenumber, root, root
            )
        logging.info('Building symbol table from tags data...done')
        return symbols

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

class SymbolFromGoto(Symbol):
    """Load symbol table from a goto binary.

    Given a goto binary, scan the symbol table in the goto binary for
    a list of symbols.  This will include every symbol used in the
    goto binary, but will omit preprocessor definitions.  Fill out
    this list of symbols and definitions by running ctags over the
    files listed in the symbol table, but definitions in the table
    take precedence over definitions inferred by ctags.  This still
    omits definitions from files that list only definitions and do not
    contribute symbols to the symbol table.
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

class SymbolFromCtags(Symbol):
    """Create a symbol table with ctags.

    Run ctags (the ctags for vi) from the given root over the given
    list of files.
    """

    # TODO: ctags by default accepts only certain file extensions
    # like .c and .h as source files.  Files with other extensions
    # like .inl are currently ignored, but consider using the ctags
    # options −−list−maps and −−langmap.

    def __init__(self, root, files):
        super().__init__(
            self.build_symbol_table(
                root, ctags_symbols(run_ctags(root, files))
            )
        )

################################################################
# Parse a ctags file
#
# This is not easy.  The default output of ctags identifies the symbol
# definition with a file name and a vi regular expression to locate
# the symbol within the file.  We use the textual output of ctags that
# gives a file name and a line number, but the textual output is
# intended to be human readable and not machine parsable.

EXUBERANT = 'exuberant'
CTAGS = 'ctags'

def have_ctags():
    """Test for existence of exuberant ctags."""

    try:
        help_banner = runt.run([CTAGS, '--help']).splitlines()[0].lower().split()
        return all(string in help_banner for string in [EXUBERANT, CTAGS])
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
    output = ''
    while files:
        paths = files[:chunk]
        files = files[chunk:]
        logging.info('Running ctags on %s files starting with %s...',
                     len(paths),
                     paths[0])
        output += runt.run([CTAGS, '-x'] + paths, cwd=root, encoding='latin1')
    logging.info('Running ctags on %s files...done', len(files))
    return output

def ctags_symbols(ctags_data):
    """Return the symbol definitions appears in a ctags file.

    Each line names a symbol, a symbol kind, a line number, and a file
    name.  The values are space-separated.
    """

    logging.info('Parsing ctag symbol definitions...')
    definitions = []
    for line in [line.strip() for line in ctags_data.splitlines()]:
        if not line:
            continue

        # ctags default output does not include line numbers.  Each
        # symbol is respresented by a symbol, a file, and a vi regular
        # expression that vi can use to find the symbol in the file.
        # This is why we use ctags -x output.
        #
        # ctags -x output is a "tabular, human-readable cross reference"
        # and is not intended to be parsable and doesn't even produce
        # tab-separated output.
        #
        # ctags -x output generally has the form
        # SYMBOL KIND LINENUMBER FILENAME CODE_FRAGMENT
        #
        # We assume filenames do not contain whitespace (false on windows)

        symbol, _, linenumber, filename = line.split()[:4]

        # However, c++ code in the source tree generates ctags -x output like
        # operator != function 80 header.h bool operator!=...
        #
        # We skip c++ symbols by checking that LINENUMBER is actual an int

        try:
            int(linenumber)
        except ValueError:
            logging.debug('Skipping unparsable ctags definition: %s', line)
            continue

        definitions.append([symbol, filename, linenumber])
    logging.info('Parsing ctag symbol definitions...done')

    return definitions

################################################################
# make-symbol

# pylint: disable=inconsistent-return-statements

def fail(msg):
    """Log failure and raise exception."""

    logging.info(msg)
    raise UserWarning(msg)

def do_make_symbol(viewer_symbol, make_source,
                   goto, wkdir, srcdir, files):
    """Implementation of make-symbol."""

    wkdir = srcloct.abspath(wkdir) if wkdir else None
    srcdir = srcloct.abspath(srcdir) if srcdir else None

    # Command line options may enable more than one way
    # to generate the symbol table, so choose the one
    # that gives the most "accurate" results.

    if viewer_symbol:
        logging.info("Symbols by SymbolFromJson")
        return SymbolFromJson(viewer_symbol)

    if make_source:
        sources = sourcet.SourceFromJson(make_source)
        srcdir = sources.root
        files = sources.files

    if srcdir and files:
        SymbolFromCtags(srcdir, files)

    if goto and wkdir and srcdir:
        logging.info("Symbols by SymbolFromGoto")
        return SymbolFromGoto(goto, wkdir, srcdir)

    fail("Unable to generate a symbol table (is ctags installed?).")

################################################################
