# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""CBMC reachable functions"""

import json
import logging
import os
import subprocess
import tempfile

import voluptuous
import voluptuous.humanize

from cbmc_viewer import filet
from cbmc_viewer import parse
from cbmc_viewer import runt
from cbmc_viewer import srcloct
from cbmc_viewer import util

JSON_TAG = 'viewer-reachable'

################################################################
# Reachable validator

VALID_REACHABLE = voluptuous.Schema({
    'reachable': {
        # file name -> list of reachable functions
        voluptuous.Optional(str): [str]
    }
}, required=True)

################################################################

class Reachable:
    """CBMC reachable functions."""

# TODO: again dicts -> dict

    def __init__(self, function_lists=None):
        """Load CBMC reachable functions from lists of functions."""

        function_lists = function_lists or []

        functions = self.merge_function_lists(function_lists)
        self.reachable = self.sort_function_names(functions)
        self.validate()

    def __repr__(self):
        """A dict representation of the reachable functions."""

        self.validate()
        return self.__dict__

    def __str__(self):
        """A string representation of the reachable functions."""

        return json.dumps({JSON_TAG: self.__repr__()}, indent=2, sort_keys=True)

    def validate(self):
        """Validate reachable functions."""

        return voluptuous.humanize.validate_with_humanized_errors(
            self.__dict__, VALID_REACHABLE
        )

    def dump(self, filename=None, directory=None):
        """Write reachable functions to a file or stdout."""

        util.dump(self, filename, directory)

    @staticmethod
    def merge_function_lists(function_lists):
        """Merge lists of functions into a single list."""

        if len(function_lists) == 1:
            return function_lists[0]

        functions = {}
        for function_list in function_lists:
            for file_name, func_names in function_list.items():
                functions[file_name] = functions.get(file_name, set())
                functions[file_name] = functions[file_name].union(func_names)

        return functions

    @staticmethod
    def sort_function_names(functions):
        """Sort the names of reachable functions in a file."""

        return {file_name: sorted(func_names)
                for file_name, func_names in functions.items()}

################################################################

class ReachableFromJson(Reachable):
    """Load the reachable functions from the output of make-reachable.

    Given a list of json files containing symbol tables produced by
    make-reachable, merge these function lists into a single list.
    """

    def __init__(self, json_files):

        super().__init__(
            [parse.parse_json_file(json_file)[JSON_TAG]["reachable"]
             for json_file in json_files]
        )

################################################################

class ReachableFromCbmcJson(Reachable):
    """Load functions from output of goto-analyzer --reachable-functions --json.
    """

    def __init__(self, json_files, root):

        super().__init__(
            [load_cbmc_json(json_file, root) for json_file in json_files]
        )

def load_cbmc_json(json_file, root):
    """Load json file produced by goto-analyzer --reachable-functions --json json_file"""

    json_data = parse.parse_json_file(json_file)
    return parse_cbmc_json(json_data, root)

# TODO: Does file-local name mangling mess this up?

def parse_cbmc_json(json_data, root):
    """Parse json output of goto-analyzer --reachable-functions --json."""

    root = srcloct.abspath(root)
    reachable = {}
    for function in json_data:
        func_name = function['function']
        if func_name.startswith('__CPROVER'):
            continue

        # goto-analyzer --reachable-functions produces a malformed
        # entry for __CPROVER_Start with an empty string for the
        # function name.
        if not func_name:
            continue

        file_name = function.get('file')
        if file_name is None:
            logging.warning('Skipping reachable function with invalid source location: %s',
                            function)
            continue

        file_name = srcloct.abspath(file_name)
        if srcloct.is_builtin(file_name):
            continue
        if not file_name.startswith(root):
            continue

        path = srcloct.relpath(file_name, root)
        reachable[path] = reachable.get(path, set())
        reachable[path].add(func_name)

    return reachable

################################################################

class ReachableFromCbmcXml(Reachable):
    """Load functions from output of goto-analyzer --reachable-functions --xml.
    """

    def __init__(self, xml_files, root):

        super().__init__([])

        _, _ = xml_files, root
        raise UserWarning("The goto-analyzer --xml option generates text "
                          "and not xml.")

################################################################

class ReachableFromGoto(Reachable):
    """Load reachable functions of a goto binary."""

    def __init__(self, goto, root, cwd=None):

        # pylint: disable=consider-using-with
        data = tempfile.NamedTemporaryFile(delete=False)

        cmd = ["goto-analyzer", "--reachable-functions", "--json", data.name, goto]
        try:
            runt.run(cmd, cwd=cwd)
        except subprocess.CalledProcessError as err:
            raise UserWarning('Failed to run {}: {}'.format(cmd, str(err))) from err

        json_data = parse.parse_json_file(data.name)
        os.unlink(data.name)

        super().__init__(
            [parse_cbmc_json(json_data, root)]
        )

################################################################
# make-reachable

# pylint: disable=inconsistent-return-statements

def fail(msg):
    """Log failure and raise exception."""

    logging.info(msg)
    raise UserWarning(msg)

def make_reachable(args):
    """The implementation of make-reachable."""

    viewer_reachable, cbmc_reachable, srcdir, goto = (
        args.viewer_reachable, args.cbmc_reachable, args.srcdir, args.goto)

    if viewer_reachable:
        if filet.all_json_files(viewer_reachable):
            return ReachableFromJson(viewer_reachable)
        fail("Expected json files: {}".format(viewer_reachable))

    if cbmc_reachable and srcdir:
        if filet.all_json_files(cbmc_reachable):
            return ReachableFromCbmcJson(cbmc_reachable, srcdir)
        if filet.all_xml_files(cbmc_reachable):
            return ReachableFromCbmcXml(cbmc_reachable, srcdir)
        fail("Expected json files or xml files, not both: {}"
             .format(cbmc_reachable))

    if goto and srcdir:
        return ReachableFromGoto(goto, srcdir)

    logging.info("make-reachable: nothing to do: need "
                 "--srcdir and --goto, or "
                 "cbmc reachable functions results (goto-analyzer --reachable-functions)"
                 " and --srcdir, or "
                 "--viewer-reachable")
    return Reachable()

################################################################
