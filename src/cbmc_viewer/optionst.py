# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Command line options."""

import argparse
import logging
import os
import platform


from cbmc_viewer import filet
from cbmc_viewer import version as viewer_version
from cbmc_viewer.sourcet import Sources

from cbmc_viewer import coveraget
from cbmc_viewer import loopt
from cbmc_viewer import propertyt
from cbmc_viewer import reachablet
from cbmc_viewer import resultt
from cbmc_viewer import sourcet
from cbmc_viewer import symbolt
from cbmc_viewer import tracet
from cbmc_viewer import viewer

choices = []
if platform.system() != 'Windows':
    choices.append('find')
choices.extend(['walk', 'make', 'goto'])

OPTION_GROUPS = [
    {'group_name': "CBMC output",
     'group_desc': """
         This is the output of CBMC that is summarized by cbmc-viewer.
         Output can be text, xml, or json, but xml is strongly preferred.""",
     'group_opts': [
         {'flag': '--result',
          'metavar': 'FILE',
          'nargs': '+',
          'help': 'CBMC property checking the results.  The output of "cbmc".'},
         {'flag': '--coverage',
          'metavar': 'FILE',
          'nargs': '+',
          'help': 'CBMC coverage checking results.  The output of "cbmc --cover locations".'},
         {'flag': '--property',
          'metavar': 'FILE',
          'nargs': '+',
          'help': 'CBMC properties checked during property checking.  '
                  'The output of "cbmc --show-properties".'}]},

    {'group_name': 'Source files',
     'group_desc': None,
     'group_opts': [
         {'flag': '--srcdir',
          'type': os.path.abspath,
          'help': 'The root of the source tree, typically the root of the code repository.'},
         {'flag': '--exclude',
          'help': """
              A regular expression for the paths relative to SRCDIR to exclude from
              the list of source files.  This is rarely used."""},
         {'flag': '--extensions',
          'metavar': 'REGEXP',
          'default': r'^\.(c|h|inl)$',
          'help': """
              A regular expression for the file extensions of files to include
              in the list of source files.  This is rarely used.  (Default: %(default)s)"""},
         {'flag': '--source-method',
          'metavar': 'MHD',
          'choices': choices,
          'help': """
               The method to use to enumerate the list of source files. This is
               rarely used.  The default method 'goto' is generally to use the files
               mentioned in the symbol table of the goto binary.  The full set of
               methods available is
               1) 'find': use the Linux 'find' command in SRCDIR,
               2) 'walk': use the Python 'walk' method in SRCDIR,
               3) 'make': use the 'make' command in the WKDIR to build the goto
                   binary with the preprocessor and use the files under SRCDIR
                   mentioned in the preprocessor output, and
               4) 'goto': use the files under SRCDIR mentioned in the symbol table
                   of the goto binary."""}]},
    {'group_name': 'GOTO binaries',
     'group_desc': None,
     'group_opts': [
         {'flag': '--wkdir',
          'default': ".",
          'type': os.path.abspath,
          'help': """
              The working directory.  This is generally the directory in which
              `goto-cc` was invoked to build the goto binary.  It is the working
              directory that is mentioned in the source locations in the goto
              binary."""},
         {'flag': '--goto',
          'help': 'The goto binary itself.'}]},

    {'group_name': 'Viewer output',
     'group_desc': None,
     'group_opts': [
         {'flag': '--reportdir',
          'default': 'report',
          'type': os.path.abspath,
          'help': """
              The report directory.  Write the final report to this
              directory.  (Default: %(default)s)"""},
         {'flag': '--json-summary',
          'metavar': 'JSON',
          'help': 'Write summary of key metrics to this json file.'}]},

    {'group_name': 'Viewer input',
     'group_desc': """
         Load json output of cbmc-viewer like "viewer-coverage.json" or the
         output of cbmc-viewer subcommands like "cbmc-viewer coverage".""",
     'group_opts': [
         {'flag': '--viewer-coverage',
          'metavar': 'JSON',
          'nargs': '+',
          'help': """
              Load the output of "cbmc-viewer" or "cbmc-viewer coverage" giving
              CBMC coverage checking results."""},
         {'flag': '--viewer-loop',
          'metavar': 'JSON',
          'nargs': '+',
          'help': """
              Load the output of "cbmc-viewer" or "cbmc-viewer loop" listing the loops
              found in the goto binary."""},
         {'flag': '--viewer-property',
          'metavar': 'JSON',
          'nargs': '+',
          'help': """
              Load the output of "cbmc-viewer" or "cbmc-viewer property" listing the properties
              checked during CBMC property checking."""},
         {'flag': '--viewer-reachable',
          'metavar': 'JSON',
          'nargs': '+',
          'help': """
              Load the output of "cbmc-viewer" or "cbmc-viewer property" listing the
              reachable functions in the goto binary."""},
         {'flag': '--viewer-result',
          'metavar': 'JSON',
          'nargs': '+',
          'help': """
              Load the output of "cbmc-viewer" or "cbmc-viewer result" giving the
              CBMC property checking results."""},
         {'flag': '--viewer-source',
          'metavar': 'JSON',
          'nargs': '+',
          'help': """
              Load the output of "cbmc-viewer" or "cbmc-viewer source" listing the source
              files used to build the goto binary."""},
         {'flag': '--viewer-symbol',
          'metavar': 'JSON',
          'nargs': '+',
          'help': """
              Load the output of "cbmc-viewer" or "cbmc-viewer symbol" listing the symbols
              in the goto binary."""},
         {'flag': '--viewer-trace',
          'metavar': 'JSON',
          'nargs': '+',
          'help': """
              Load the output of "cbmc-viewer" or "cbmc-viewer trace" giving the error traces
              generated by CBMC for the issues found during property checking."""}]},

    {'group_name': 'Other',
     'group_desc': None,
     'group_opts': [
         {'flag': '--verbose',
          'action': 'store_true',
          'help': 'Verbose output.'},
         {'flag': '--debug',
          'action': 'store_true',
          'help': 'Debugging output.'},
         {'flag': '--version',
          'action': 'version',
          'version': viewer_version.version(),
          'help': 'Display version number and exit.'},
         {'flag': '--config',
          'metavar': 'JSON',
          'default': "cbmc-viewer.json",
          'help': """
              Viewer configuration file used (for example) to list the functions
              intentionally omitted from the verification.  (Default: '%(default)s')"""}]},

    {'group_name': 'Deprecated',
     'group_desc': 'Options from prior versions now deprecated.',
     'group_opts': [
         {'flag': '--block',
          'metavar': 'BLOCK',
          'help': 'Use --coverage instead.'},
         {'flag': '--htmldir',
          'metavar': 'HTMLDIR',
          'help': 'Use --reportdir instead.'},
         {'flag': '--srcexclude',
          'metavar': 'EXCLUDE',
          'help': 'Use --exclude instead.'},
         {'flag': '--blddir',
          'help': 'Ignored.'},
         {'flag': '--storm',
          'help': 'Ignored.'}]}
]

SUBPARSERS = [
    {'name': None,
     'func': viewer.viewer,
     'desc': 'Generate a browsable summary of CBMC results',
     'flags': None},
    {'name': 'coverage',
     'func': coveraget.make_and_save_coverage,
     'desc': 'Summarize coverage checking results',
     'flags': ['--coverage', '--viewer-coverage', '--srcdir']},
    {'name': 'loop',
     'func': loopt.make_and_save_loop,
     'desc': 'List loops found in the goto binary',
     'flags': ['--viewer-loop', '--goto', '--srcdir']},
    {'name': 'property',
     'func': propertyt.make_and_save_property,
     'desc': 'List properties checked for during property checking',
     'flags': ['--property', '--viewer-property', '--srcdir']},
    {'name': 'reachable',
     'func': reachablet.make_and_save_reachable,
     'desc': 'List reachable functions in the goto binary',
     'flags': ['--viewer-reachable', '--goto', '--srcdir']},
    {'name': 'result',
     'func': resultt.make_and_save_result,
     'desc': 'Summarize CBMC property checking results',
     'flags': ['--result', '--viewer-result']},
    {'name': 'source', # TODO: add --files back
     'func': sourcet.make_and_save_source,
     'desc': 'List source files used to build the goto binary',
     'flags': ['--viewer-source', '--goto', '--srcdir', '--wkdir',
               '--source-method', '--extensions', '--exclude']},
    {'name': 'symbol',  # TODO: add --files back
     'func': symbolt.make_and_save_symbol,
     'desc': 'List symbols found in the goto binary',
     'flags': ['--viewer-symbol', '--viewer-source', '--goto', '--wkdir', '--srcdir']},
    {'name': 'trace',
     'func': tracet.make_and_save_trace,
     'desc': 'List error traces generated for issues found during property checking',
     'flags': ['--result', '--viewer-trace', '--wkdir', '--srcdir']},
]

def add_arguments(parser, function=None, flags=None):
    """Add implementing function and list of flags to a parser"""

    if function:
        parser.set_defaults(func=function)
    if flags:
        flags = flags + ['--verbose', '--debug', '--version']

    for group in OPTION_GROUPS:
        options = [
            option for option in group['group_opts'] if flags is None or option['flag'] in flags]
        if not options:
            continue

        parser_group = parser.add_argument_group(group['group_name'], group['group_desc'])
        for option in options:
            opt = dict(option) # pop is destructive
            flag = opt.pop('flag')
            parser_group.add_argument(flag, **opt)

def add_subparser(subparsers, sub_name, sub_desc, sub_func, sub_flags):
    """Add a defined subparser"""

    if sub_name:
        subparser = subparsers.add_parser(sub_name, description=sub_desc)
    add_arguments(subparser, sub_func, sub_flags)

def create_parser():
    """Create the parser with defined subparsers"""

    top = SUBPARSERS[0]
    assert top['name'] is None

    parser = argparse.ArgumentParser(description=top['desc'])
    add_arguments(parser, top['func'], top['flags'])

    subparsers = parser.add_subparsers(title='Subcommands', dest='subcommand')
    for subparser in SUBPARSERS[1:]:
        add_subparser(subparsers,
                      subparser['name'], subparser['desc'], subparser['func'], subparser['flags'])
    return parser

################################################################

def handle_deprecated_arguments(args):
    """Warn about deprecated arguments, use them  when possible."""

    if hasattr(args, 'block') and args.block:
        if hasattr(args, 'coverage'):
            logging.warning("--block is deprecated, using --coverage %s.",
                            args.block)
            args.coverage = [args.block] # block is a string, coverage is a list
        else:
            logging.warning("--block is deprecated, use --coverage instead.")
        args.block = None

    if hasattr(args, 'htmldir') and args.htmldir:
        if hasattr(args, 'reportdir'):
            logging.warning("--htmldir is deprecated, using --reportdir %s.",
                            args.htmldir)
            args.reportdir = args.htmldir
        else:
            logging.warning("--htmldir is deprecated, use --reportdir instead.")
        args.htmldir = None

    if hasattr(args, 'srcexclude') and args.srcexclude:
        if hasattr(args, 'exclude'):
            logging.warning("--srcexclude is deprecated, using --exclude %s.",
                            args.srcexclude)
            args.exclude = args.srcexclude
        else:
            logging.warning("--srcexclude is deprecated, "
                            "use --exclude instead.")
        logging.warning("--srcexclude and --exclude use slight different "
                        "regular expressions.")
        args.srcexclude = None

    if hasattr(args, 'blddir') and args.blddir:
        logging.warning("--blddir is deprecated, ignoring --blddir.")
        args.blddir = None

    if hasattr(args, 'storm') and args.storm:
        logging.warning("--storm is deprecated, ignoring --storm.")
        args.storm = None

    return args

################################################################
# Set default values for arguments

def default_logging(args):
    'Set default logging configuration.'

    # Only the first invocation of basicConfig configures the root logger
    if getattr(args, 'debug', False):
        logging.basicConfig(level=logging.DEBUG,
                            format='%(levelname)s: %(message)s')
    if getattr(args, 'verbose', False):
        logging.basicConfig(level=logging.INFO,
                            format='%(levelname)s: %(message)s')
    logging.basicConfig(format='%(levelname)s: %(message)s')

    return args

def default_source_method(args):
    'Set default source method.'

    # Set source_method to an enum
    if hasattr(args, 'source_method'):

        # Set source method to its enum value or None
        args.source_method = {
            'find': Sources.FIND,
            'walk': Sources.WALK,
            'make': Sources.MAKE,
            'goto': Sources.GOTO,
            None: None
        }[args.source_method]

        # Set source method to a reasonable default value
        if args.source_method is None:
            if getattr(args, 'srcdir') is not None:
                if getattr(args, 'wkdir') is not None:
                    if getattr(args, 'goto') is not None:
                        args.source_method = Sources.GOTO
                    else:
                        args.source_method = Sources.MAKE
                elif platform.system() == 'Windows':
                    args.source_method = Sources.WALK
                else:
                    args.source_method = Sources.FIND

        # Confirm existence of command line options needed by source method
        if args.source_method == Sources.GOTO:
            if (not hasattr(args, 'srcdir') or
                    not hasattr(args, 'wkdir') or
                    not hasattr(args, 'goto')):
                raise UserWarning('Options --srcdir, --wkdir, and --goto '
                                  'required by source method goto.')

        if args.source_method == Sources.FIND:
            if not hasattr(args, 'srcdir'):
                raise UserWarning('Option --srcdir required '
                                  'by source method find.')

        if args.source_method == Sources.WALK:
            if not hasattr(args, 'srcdir'):
                raise UserWarning('Option --srcdir required '
                                  'by source method walk.')

        if args.source_method == Sources.MAKE:
            if not hasattr(args, 'srcdir') or not hasattr(args, 'wkdir'):
                raise UserWarning('Options --srcdir and --wkdir required '
                                  'by source method make.')

    return args

def warn_against_using_text_for_cbmc_output(args):
    'Recommend the use of xml or json input instead of text.'

    for attr in ['result', 'coverage', 'property']:
        filenames = getattr(args, attr, None)
        if filenames and filet.any_text_files(filenames):
            logging.warning("Use xml or json instead of text for "
                            "better results: %s", filenames)

def defaults(args):
    'Set default values based on command line arguments.'

    args = default_logging(args)
    args = handle_deprecated_arguments(args)
    args = default_source_method(args)
    warn_against_using_text_for_cbmc_output(args)

    if hasattr(args, 'srcdir') and args.srcdir is not None:
        args.srcdir = os.path.abspath(args.srcdir)
    if hasattr(args, 'wkdir') and args.wkdir is not None:
        args.wkdir = os.path.abspath(args.wkdir)

    return args

################################################################
