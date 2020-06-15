# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""The symbols used to build a goto binary."""

import enum
import json
import logging
import os

import voluptuous

import parse
import runt
import sourcet
import srcloct
import symbol_table
import util

JSON_TAG = 'viewer-symbol'

################################################################

class Tags(enum.Enum):
    """Enum values for --tags_method command line option"""

    CTAGS = 1
    ETAGS = 2

################################################################
# Data validator for symbol object

VALID_SYMBOL = voluptuous.schema_builder.Schema(
    {
        'symbols': {
            # symbol name -> symbol srcloc
            str : srcloct.VALID_SRCLOC
        }
    }
)

################################################################

class Symbol:
    """The symbols used to build a goto binary."""

    def __init__(self, symbols):

        self.symbols = symbols

        # show progress: symbol validation can be slow on large tables
        logging.info('Validating symbol definitions...')
        VALID_SYMBOL(self.__dict__)
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

    @staticmethod
    def build_symbol_table(root, definitions):
        """Build a symbol table using parsed output of ctags or etags."""

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

        super(SymbolFromJson, self).__init__(
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

        super(SymbolFromGoto, self).__init__(symbols)

################################################################

class SymbolFromCtags(Symbol):
    """Create a symbol table with ctags.

    Run ctags (the ctags for vi) from the given root over the given
    list of files.
    """

    def __init__(self, root, files):
        super(SymbolFromCtags, self).__init__(
            self.build_symbol_table(
                root, ctags_symbols(run_ctags(root, files))
            )
        )

################################################################

class SymbolFromEtags(Symbol):
    """Create a symbol table with etags (the emacs ctags).

    Run etags (the ctags for emacs) from the given root over the given
    list of files.
    """

    def __init__(self, root, files):
        super(SymbolFromEtags, self).__init__(
            self.build_symbol_table(
                root, etags_symbols(run_etags(root, files))
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
# Parse an etags file
#
# The etags format is described at https://en.wikipedia.org/wiki/Ctags#Etags_2

ETAGS = 'etags'
TAGS = 'TAGS' + '-' + str(os.getpid())

def have_etags():
    """Test for the existence of etags."""

    try:
        help_banner = runt.run([ETAGS, '--help']).splitlines()[0].lower().split()
        return ETAGS in help_banner
    except FileNotFoundError:
        return False

def run_etags(root, files, chunk=2000):
    """Run etags from the given root over the given files.

    Some operating systems limit the number of command line arguments
    (or the length of the command), we we process the list of files in
    chunks.
    """

    if not files:
        return ''

    try:
        os.remove(TAGS)
    except FileNotFoundError:
        pass # file did not exist

    logging.info('Running etags on %s files...', len(files))
    while files:
        paths = files[:chunk]
        files = files[chunk:]
        logging.info('Running etags on %s files starting with %s...',
                     len(paths),
                     paths[0])
        runt.run([ETAGS, '-o', TAGS, '--append'] + paths,
                 cwd=root, encoding='latin1')
    logging.info('Finished running etags.')

    with open(os.path.join(root, TAGS)) as etags_file:
        etags_data = etags_file.read()
    os.remove(os.path.join(root, TAGS))
    return etags_data

def etags_symbols(etags_data):
    """Return the symbol definitions appearing in an etags file.

    Scan etags_data, the contents of an etags file, and return the
    list of symbol definitions in the file as a list of tuples of the
    form [symbol, filename, linenumber].
    """

    logging.info('Parsing etag symbol definitions...')
    # Each section begins with a line containing just "\f"
    sections = etags_data.split('\f\n')[1:]
    symbols = [definition
               for section in sections
               for definition in etags_section_definitions(section)]
    logging.info('Finished parsing etag symbol definitions.')
    return symbols

def etags_section_definitions(section):
    """Return the symbol definitions in a section of an etags file.

    A section consists of a sequence of lines: a header containing a
    file name, and a sequence of definitions containing symbols and
    line numbers.
    """

    lines = section.splitlines()
    filename = etags_section_filename(lines[0])
    return [[symbol, filename, num]
            for symbol, num in [etags_symbol_definition(line)
                                for line in lines[1:]]
            if symbol is not None]

def etags_section_filename(header):
    """Return the file name in the section header.

    A section header is a filename and a section length separated by a
    comma.
    """
    return header.split(',')[0]

def etags_symbol_definition(definition):
    """Return the symbol and line number in a symbol definition.

    A symbol definition is the symbol definition, '\x7f', the symbol
    name, '\x01, the line number, ',', and the offset within the file.
    The symbol name is omitted if it can be easily located in the
    symbol definition.
    """

    try:
        tag_def, tag_name_line_offset = definition.split('\x7f')
        tag_name_line, _ = tag_name_line_offset.split(',')
        tag_name, tag_line = ([None] + tag_name_line.split('\x01'))[-2:]
        if tag_name is None:
            tag_name = tag_def.split()[-1].lstrip('(')
        tag_name = tag_name.rstrip('()[].,;')
    except ValueError:
        logging.debug('Skipping unparsable etags definition: %s', definition)
        return None, 0

    return tag_name, int(tag_line)

################################################################
# make-symbol

# pylint: disable=inconsistent-return-statements

def fail(msg):
    """Log failure and raise exception."""

    logging.info(msg)
    raise UserWarning(msg)

def validate_option_groups(viewer_symbol, make_source, goto,
                           wkdir, srcdir, files):
    """Check mutually exclusive groupings of command line options."""

    groups = [viewer_symbol is not None,
              make_source is not None,
              goto is not None and wkdir is not None and srcdir is not None,
              srcdir is not None and files is not None]
    if len([group for group in groups if group]) != 1:
        fail("Specify --symbols, --sources, or --srcdir and --files.")

def do_make_symbol(viewer_symbol, make_source, tags_method,
                   goto, wkdir, srcdir, files):
    """Implementation of make-symbol."""

    wkdir = srcloct.abspath(wkdir) if wkdir else None
    srcdir = srcloct.abspath(srcdir) if srcdir else None

    validate_option_groups(viewer_symbol, make_source, goto,
                           wkdir, srcdir, files)

    if viewer_symbol:
        logging.info("Symbols by SymbolFromJson")
        return SymbolFromJson(viewer_symbol)

    if goto and wkdir and srcdir:
        logging.info("Symbols by SymbolFromGoto")
        return SymbolFromGoto(goto, wkdir, srcdir)

    if make_source:
        sources = sourcet.SourceFromJson(make_source)
        srcdir = sources.root
        files = sources.files

    if srcdir and files:
        # tags_method was set to a reasonable value by optionst.defaults()
        # if it was not specified on the command line.
        if tags_method == Tags.CTAGS:
            logging.info("Symbols by SymbolFromCtags")
            return SymbolFromCtags(srcdir, files)
        if tags_method == Tags.ETAGS:
            logging.info("Symbols by SymbolFromEtags")
            return SymbolFromEtags(srcdir, files)

    fail("Unable to generate a symbol table (is ctags installed?).")

################################################################
