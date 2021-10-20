# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Command line options."""

import logging
import os
import platform

from cbmc_viewer import filet
from cbmc_viewer import version as viewer_version
from cbmc_viewer.sourcet import Sources

def goto(parser):
    'Define --goto command line option.'

    parser.add_argument(
        '--goto',
        help="""
        The goto binary.
        """
    )
    return parser

def srcdir(parser):
    'Define --srcdir command line option.'

    parser.add_argument(
        '--srcdir',
        type=os.path.abspath,
        help="""
        The source directory.  The root of the source tree.
        """
    )
    return parser

def wkdir(parser):
    'Define --wkdir command line option.'

    parser.add_argument(
        '--wkdir',
        default=".",
        type=os.path.abspath,
        help="""
        The working directory in source locations in the goto binary
        (and omitted when source locations are printed in textual form).
        This is usually the directory in which goto-cc was invoked to
        build the goto binary.
        """
    )
    return parser

def reportdir(parser):
    'Define --reportdir command line option.'

    parser.add_argument(
        '--reportdir',
        default='report',
        type=os.path.abspath,
        help="""
        The report directory.  Write the final report to this directory.
        (Default: %(default)s)
        """
    )
    return parser

def result(parser):
    'Define --result command line option.'

    parser.add_argument(
        '--result',
        metavar='FILE',
        nargs='+',
        help="""
        CBMC property checking results.
        A text, xml, or json file containing the output of 'cbmc'.
        """
    )
    return parser

def coverage(parser):
    'Define --coverage command line option.'

    parser.add_argument(
        '--coverage',
        metavar='FILE',
        nargs='+',
        help="""
        CBMC coverage checking results.
        An xml or json file containing the output of
        'cbmc --cover locations'.
        """
    )
    return parser

def property(parser):
    'Define --property command line option.'

    # pylint: disable=redefined-builtin

    parser.add_argument(
        '--property',
        metavar='FILE',
        nargs='+',
        help="""
        CBMC properties checked during property checking.
        An xml or json file containing the output of
        'cbmc --show-properties'.
        """
    )
    return parser

def exclude(parser):
    'Define --exclude command line option.'

    parser.add_argument(
        '--exclude',
        help="""
        Paths relative to SRCDIR to exclude from the list of source files.
        A Python regular expression matched against the result
        of os.path.normpath().  The match is case insensitive.
        """
    )
    return parser

def extensions(parser):
    'Define --extensions command line option.'

    parser.add_argument(
        '--extensions',
        metavar='REGEXP',
        default=r'^\.(c|h|inl)$',
        help="""
        File extensions of files to include in the list of source files.
        A Python regular expression matched against the result of
        os.path.splitext().  The match is case insensitive.
        (Default: %(default)s)
        """
    )
    return parser

def source_method(parser):
    'Define --source-method command line option.'

    choices = []
    if platform.system() != 'Windows':
        choices.append('find')
    choices.extend(['walk', 'make', 'goto'])

    parser.add_argument(
        '--source-method',
        metavar='MHD',
        choices=choices,
        help="""
        The method to use to list source files under SRCDIR.  Methods
        available are [%(choices)s]: Use the Linux 'find' command, use
        the Python 'walk' method, use the 'make' command to build
        the goto binary with the preprocessor, or use the symbol table in
        the goto binary.  The default method is 'goto' if
        SRCDIR and WKDIR and GOTO are specified, 'make' if SRCDIR and WKDIR
        are specified, 'walk' on Windows, and 'find' otherwise.
        """
    )
    return parser

def config(parser):
    'Define --config command line option.'

    parser.add_argument(
        '--config',
        metavar='JSON',
        default="cbmc-viewer.json",
        help="""
        JSON configuration file. (Default: '%(default)s')
        """
    )
    return parser

################################################################
# Load data from the make-* commands

def viewer_reachable(parser):
    "Load make-reachable data"

    parser.add_argument(
        '--viewer-reachable',
        metavar='JSON',
        nargs='+',
        help='Load reachable functions from the JSON output of make-reachable.'
        ' If multiple files are given, merge multiple data sets into one.'
    )

def viewer_coverage(parser):
    "Load make-coverage data"

    parser.add_argument(
        '--viewer-coverage',
        metavar='JSON',
        nargs='+',
        help='Load coverage data from the JSON output of make-coverage.'
        ' If multiple files are given, merge multiple data sets into one.'
    )

def viewer_loop(parser):
    "Load make-loop data"

    parser.add_argument(
        '--viewer-loop',
        metavar='JSON',
        nargs='+',
        help='Load loops from the JSON output of make-loop.'
        ' If multiple files are given, merge multiple data sets into one.'
    )

def viewer_property(parser):
    "Load make-property data"

    parser.add_argument(
        '--viewer-property',
        metavar='JSON',
        nargs='+',
        help='Load properties from the JSON output of make-property.'
        ' If multiple files are given, merge multiple data sets into one.'
    )

def viewer_result(parser):
    "Load make-result data"


    parser.add_argument(
        '--viewer-result',
        metavar='JSON',
        nargs='+',
        help='Load results from the JSON output of make-result.'
        ' If multiple files are given, merge multiple data sets into one.'
    )

def viewer_source(parser):
    "Load make-source data"

    parser.add_argument(
        '--viewer-source',
        metavar='JSON',
        nargs='+',
        help='Load sources from the JSON output of make-source.'
        ' If multiple files are given, merge multiple data sets into one.'
    )
def viewer_symbol(parser):
    "Load make-symbol data"

    parser.add_argument(
        '--viewer-symbol',
        metavar='JSON',
        nargs='+',
        help='Load symbols from the JSON output of make-symbol.'
        ' If multiple files are given, merge multiple data sets into one.'
    )

def viewer_trace(parser):
    "Load make-trace data"

    parser.add_argument(
        '--viewer-trace',
        metavar='JSON',
        nargs='+',
        help='Load traces from the JSON output of make-trace.'
        ' If multiple files are given, merge multiple data sets into one.'
    )
    return parser

################################################################
# Other line options

def log(parser):
    'Define --verbose and --debug command line options.'

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output.'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Debugging output.'
    )
    return parser

def version(parser):
    'Define --version command line option.'

    parser.add_argument(
        '--version',
        action='version',
        version=viewer_version.version(),
        help="""Display version number and exit."""
    )
    return parser

################################################################
# Depricated command line options
#
# Handle command line options from prior versions of cbmc-viewer that
# are deprecated in the current version.  Some old options have
# natural equivalents among the new options, some have a slight change
# in semantics that aren't easy to fix, and some we no longer support.

def block(parser):
    'Define --block command line option.'
    parser.add_argument(
        '--block',
        metavar='BLOCK',
        help="""Use --coverage instead."""
    )
    return parser

def htmldir(parser):
    'Define --htmldir command line option.'
    parser.add_argument(
        '--htmldir',
        metavar='HTMLDIR',
        help="""Use --reportdir instead."""
    )
    return parser

def srcexclude(parser):
    'Define --srcexclude command line option.'
    parser.add_argument(
        '--srcexclude',
        metavar='EXCLUDE',
        help="""Use --exclude instead."""
    )
    return parser

def blddir(parser):
    'Define --blddir command line option.'
    parser.add_argument(
        '--blddir',
        help="""Ignored."""
    )
    return parser

def storm(parser):
    'Define --storm command line option.'
    parser.add_argument(
        '--storm',
        help="""Ignored."""
    )
    return parser

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
