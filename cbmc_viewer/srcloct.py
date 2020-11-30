# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Manipulate source locations and path names appearing in CBMC output."""

import logging
import os
import re

import voluptuous

################################################################
# The following functions extract the names of builtin functions from
# path names that appear in source locations.
#
# CBMC uses names like <builtin-library-malloc> for the builtin models
# of functions like malloc in the standard library.  CBMC uses path
# names like /usr/project/testing/<builtin-malloc> for these builtin
# functions in source locations that appear in places like traces.

def builtin_name(path):
    """Return the builtin function named in the path."""

    name = os.path.basename(path).strip()
    if name.startswith('<') and name.endswith('>'):
        return name
    return None

def is_builtin(path):
    """Does path name a builtin function?"""

    return builtin_name(path) is not None

################################################################
# The following functions transform pathnames into a canonical form.
#
# We define the canonical form to be a path using the Linux path
# separator.  The canonical form of a windows path "c:\users\foo" is
# "c:/users/foo".
#
# On Windows, the os.path functions accept both / and \ as path
# separators, but os.path.normpath and os.path.abspath return paths
# using \.

def normpath(path):
    """Return a normalized path in canonical form."""

    return os.path.normpath(path).replace(os.sep, '/')

def abspath(path):
    """ Return an absolute path in canonical form."""

    return os.path.abspath(path).replace(os.sep, '/')

def relpath(path, root):
    """Return a relative path in canonical form.

    Return a relative path from root to path if path is under root,
    and return path itself if it is not.
    """

    path = normpath(path)
    root = normpath(root)

    if path.startswith(root+'/'):
        # normpath returns "." for the empty string when path == root
        return normpath(path[len(root)+1:])
    return path

################################################################
# The following functions parse source locations into a canonical form.
#
# A CBMC source location consists of a file name, a function name, a
# line number, and a working directory.  The file name is either an
# absolute path or a relative path relative to the working directory.
#
# A viewer source location is a file name, a function name, and a line
# number.  The file name is either an absolute path or a relative path
# relative to the root of the source tree.
#
# CBMC represents source locations differently in its text, json, and
# xml output.  In json and xml, the working directory is given by
# different keys.  In text, the working directory is omitted.
#
# When working with CBMC source locations in text output, we need to
# be told the working directory.  The working directory in a CBMC
# source location is generally the directory in which goto-cc is
# invoked.  We assume this is the directory containing the final goto
# binary --- specified with --wkdir on the command line --- and we
# use this as the working directory when working with CBMC source
# locations in text output.
#
# This assumption can be false, and it is hard to test this assumption
# in cases where the goto binary is built on one machine and the
# report is generated on another.  In this case, the list of errors
# and error traces will still be correct, but links into the source
# code will be wrong and source code coverage data use the wrong
# filenames.

# TODO: Consider replacing the srcloc dict with a srcloc class.

VALID_SRCLOC = voluptuous.schema_builder.Schema(
    {"file": str, "function": voluptuous.Any(None, str), "line": int},
    required=True
)

################################################################
# A "missing source location" for use when the source location really
# is missing from cbmc output, or when the source location might
# otherwise point to code outside of the source tree (like an inlined
# function definition in a system header file).

MISSING = 'MISSING'
MISSING_SRCLOC = {'file': MISSING, 'function': MISSING, 'line': 0}

def is_missing(name):
    """The name of a file or function is missing."""
    return name == MISSING

################################################################
# Construct a viewer source location from cbmc source locations
# appearing in cbmc output.

def make_srcloc(path, func, line, wkdir, root):
    """Make a viewer source location from a CBMC source location."""

    if path is None or line is None:
        logging.info("Generating a viewer srcloc for a missing CBMC srcloc.")
        return MISSING_SRCLOC

    path = normpath(path)
    if is_builtin(path):
        path = builtin_name(path)
    else:
        if wkdir is not None:
            path = normpath(os.path.join(normpath(wkdir), path))
        if root is not None:
            path = relpath(path, normpath(root))

    if line is not None:
        line = int(line)

    return {'file': path, 'function': func, 'line': line}

def text_srcloc(cbmc_srcloc, wkdir=None, root=None):
    """Parse a CBMC source location in text output."""

    # Source locations appear in many forms in text output

    # Source location in a step
    match = re.search('file (.+) function (.+) line ([0-9]+)', cbmc_srcloc)
    if match:
        path, func, line = match.groups()[:3]
        return make_srcloc(path, func, line, wkdir, root)

    # Source location in an assumption
    match = re.search('file (.+) line ([0-9]+) function (.+)', cbmc_srcloc)
    if match:
        path, line, func = match.groups()[:3]
        return make_srcloc(path, func, line, wkdir, root)

    # Source location in an intrinsic step may omit file and line
    match = re.search('function (.+) thread', cbmc_srcloc)
    if match:
        path, func, line = '<intrinsic>', match.group(1), 0
        return make_srcloc(path, func, line, wkdir, root)

    logging.info("Source location missing in text output: %s", cbmc_srcloc)
    return None

def json_srcloc(cbmc_srcloc, root=None):
    """Parse a CBMC source location in json output."""

    # json output omits source locations in traces
    if cbmc_srcloc is None:
        logging.info("Source location missing in json output.")
        return make_srcloc(None, None, None, None, None)

    return make_srcloc(
        cbmc_srcloc.get('file'),
        cbmc_srcloc.get('function'),
        cbmc_srcloc.get('line'),
        cbmc_srcloc.get('workingDirectory'),
        root
    )

def xml_srcloc(cbmc_srcloc, root=None):
    """Parse a CBMC source location in xml output."""

    # xml output omits source locations in traces
    if cbmc_srcloc is None:
        logging.info("Source location missing in xml output.")
        return make_srcloc(None, None, None, None, None)

    return make_srcloc(
        cbmc_srcloc.get('file'),
        cbmc_srcloc.get('function'),
        cbmc_srcloc.get('line'),
        cbmc_srcloc.get('working-directory'),
        root
    )

################################################################
