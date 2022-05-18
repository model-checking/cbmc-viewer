"""Ctags support for locating symbol definitions"""

from pathlib import Path
import json
import logging

from cbmc_viewer import runt
from cbmc_viewer import srcloct

################################################################

def ctags(root, files):
    """List symbols defined in files under root."""

    root = Path(root)
    files = [str(file_) for file_ in files]
    return (universal_ctags(root, files) or
            exhuberant_ctags(root, files) or
            legacy_ctags(root, files) or
            [])

def symbols(root, files):
    """Map symbol names to source locations for symbols defined in files under root."""

    def well_typed_tags(tag):
        """Ensure tag has the correct type"""

        try:
            symbol_, file_, line_ = str(tag['symbol']), str(tag['file']), int(tag['line'])
            assert symbol_ and file_ and line_
            return [{'symbol': symbol_, 'file': file_, 'line': line_}]
        except (AssertionError, ValueError, KeyError):
            logging.info('Skipping tag: "%s"', tag)
            return []

    tags = ctags(root, files)
    tags = [tag_ for tag in tags for tag_ in well_typed_tags(tag)]
    tags = sorted(tags, key=lambda tag: (tag['symbol'], tag['file'], tag['line']))

    symbol_map = {}
    for tag in tags:
        symbol = tag['symbol']
        if symbol in symbol_map:
            logging.info('Skipping tag: "%s"', tag)
            continue
        symbol_map[symbol] = srcloct.make_srcloc(tag['file'], None, tag['line'], root, root)
    return symbol_map


################################################################

def universal_ctags(root, files):
    """Use universal ctags to list symbols defined in files under root."""

    # See universal ctags man page at https://docs.ctags.io/en/latest/man/ctags.1.html
    cmd = [
        'ctags',
        '-L', '-', # read files from standard input, one file per line
        '-f', '-', # write tags to standard output, one tag per line
        '--output-format=json', # each tag is a one-line json blob
        '--fields=FNnK' # json blob is {"name": symbol, "path": file, "line": line, "kind": kind}
    ]
    try:
        logging.info("Running universal ctags")
        stdout, _ = runt.popen(cmd, cwd=root, stdin='\n'.join(files))
        strings = stdout.splitlines()
    except UserWarning:
        logging.info("Universal ctags failed")
        strings = []

    return [tag for string in strings for tag in universal_tag(root, string)]

def universal_tag(root, string):
    """Extract tag from universal ctag output."""

    try:
        # universal ctag json output is '{"name": symbol, "path": file, "line": line, "kind": kind}'
        blob = json.loads(string)
        return [{'symbol': blob['name'], 'file': root/blob['path'], 'line': int(blob['line']),
                 'kind': blob['kind']}]
    except (json.decoder.JSONDecodeError, # json is unparsable
            KeyError,                     # json key is missing
            ValueError) as error:         # invalid literal for int()
        logging.debug("Bad universal ctag: %s: %s", string, error)
        return []

################################################################

def exhuberant_ctags(root, files):
    """Use exhuberant ctags to list symbols defined in files under root."""

    # See exhuberant ctags man page at ...
    cmd = [
        'ctags',
        '-L', '-', # read files from standard input, one file per line
        '-f', '-', # write tags to standard output, one tag per line
        '-n', # use line numbers (not search expressions) to locate symbol in file
        '--fields=K' # include symbol kind among extension fields
    ]
    try:
        logging.info("Running exhuberant ctags")
        stdout, _ = runt.popen(cmd, cwd=root, stdin='\n'.join(files))
        strings = stdout.splitlines()
    except UserWarning:
        logging.info("Exhuberant ctags failed")
        strings = []

    return [tag for string in strings for tag in exhuberant_tag(root, string)]

def exhuberant_tag(root, string):
    """Extract tag from exhuberant ctag output."""

    try:
        # exhuberant ctag output is 'symbol<TAB>path<TAB>line;"<TAB>kind'
        left, right = string.split(';"')[:2]
        symbol, path, line = left.split("\t")[:3]
        kind = right.split("\t")[1]
        return [{'symbol': symbol, 'file': root/path, 'line': int(line), 'kind': kind}]
    except (ValueError, IndexError): # not enough values to unpack, invalid literal for int()
        logging.debug('Bad exhuberant ctag: "%s"', string)
        return []

################################################################

def legacy_ctags(root, files):
    """Use legacy ctags to list symbols defined in files under root."""

    cmd = ['ctags',
           '-x',  # write human-readable summary to standard output
           *files # legacy ctags cannot read list of files from stdin
    ]
    try:
        logging.info("Running legacy ctags")
        stdout, _ = runt.popen(cmd, cwd=root)
        strings = stdout.splitlines()
    except UserWarning:
        logging.info("Legacy ctags failed")
        strings = []
    print(strings)
    return [tag for string in strings for tag in legacy_tag(root, string)]

def legacy_tag(root, string):
    """Extract tag from legacy ctag output."""

    try:
        # legacy ctag -x output is 'symbol line path source_code_fragment'
        symbol, line, path = string.split()[:3]
        return [{'symbol': symbol, 'file': root/path, 'line': int(line), 'kind': None}]
    except ValueError: # not enough values to unpack, invalid literal for int()
        logging.debug('Bad legacy ctag: "%s"', string)
        return []

################################################################
