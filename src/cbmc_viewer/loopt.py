# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""CBMC loop information"""

import json
import logging
import re
import subprocess

import voluptuous
import voluptuous.humanize

from cbmc_viewer import filet
from cbmc_viewer import parse
from cbmc_viewer import runt
from cbmc_viewer import srcloct
from cbmc_viewer import util

JSON_TAG = 'viewer-loop'

################################################################
# Loop validator

VALID_LOOP = voluptuous.Schema({
    'loops': {
        # loop name -> loop srcloc
        voluptuous.Optional(str): srcloct.VALID_SRCLOC
    }
}, required=True)

################################################################

class Loop:
    """CBMC loop information."""

    def __init__(self, loop_maps=None):
        """Load CBMC loop map from a lists of loop maps."""

        loop_maps = loop_maps or []

        def handle_duplicates(name, srcloc1, srcloc2):
            logging.warning("Found duplicate loop definition: "
                            "%s: %s %s <- %s %s",
                            name,
                            srcloc1["file"],
                            srcloc1["line"],
                            srcloc2["file"],
                            srcloc2["line"])

        self.loops = util.merge_dicts(loop_maps, handle_duplicates)
        self.loops = self.unmangle_loop_names(self.loops)
        self.validate()

    def __repr__(self):
        """A dict representation of the loop table."""

        self.validate()
        return self.__dict__

    def __str__(self):
        """A string representation of the loop table."""

        return json.dumps({JSON_TAG: self.__repr__()}, indent=2, sort_keys=True)

    def validate(self):
        """Validate loops."""

        return voluptuous.humanize.validate_with_humanized_errors(
            self.__dict__, VALID_LOOP
        )

    def dump(self, filename=None, directory=None):
        """Write loops to a file or stdout."""

        util.dump(self, filename, directory)


# TODO: generally don't fail silently, give warning or raise exception
# TODO: generally give hints for how to fix the problem (give actions to take)

    @staticmethod
    def unmangle_loop_names(loops):
        """Reverse CBMC name mangling of loop names in static functions."""

        # Loops in static function FUNC may have names FUNC$link1.0
        static_names = [name for name in loops if '$link' in name]

        # Replace the name FUNC$link1.0 with FUNC.0
        for long_name in static_names:
            long_func, index = long_name.split('.')
            short_func = long_func.split('$')[0]
            short_name = '{}.{}'.format(short_func, index)
            assert long_name != short_name

            if short_name in loops:
                if loops[short_name] != loops[long_name]:
                    logging.warning("Found duplicate loop definition: "
                                    "%s: %s %s <- %s %s",
                                    short_name,
                                    loops[short_name]["file"],
                                    loops[short_name]["line"],
                                    loops[long_name]["file"],
                                    loops[long_name]["line"])
                continue
            loops[short_name] = loops[long_name]
            del loops[long_name]
        return loops

    def names(self):
        """Loop names."""

        return self.loops.keys()

    def lookup(self, name):
        """Look up the srcloc for the named loop."""

        return self.loops.get(name)

    def lookup_static(self, name):
        """Look up the srcloc for the named loop in a static function."""

        # CBMC property checking refers to loop K in function FCN as FCN.K,
        # but the goto-cc --export-file-local-symbols flag renames FCN.K
        # appearing in a file FILE in a static function FCN as
        # __CPROVER_file_local_FILE_FCN_LOOP.N
        keys = [key for key in self.loops.keys() if key.endswith('_'+name)]
        if not keys:
            return None
        if len(keys) != 1:
            raise UserWarning("Loop name {} matches {} static loop names: {}"
                              .format(name, len(keys), keys))

        return self.loops.get(keys[0])

    def lookup_assertion(self, name):
        """Look up the srcloc for the named loop unwinding assertion."""

        # CBMC refers to the loop K in function FCN as FCN.K and to
        # the unwinding assertion associated with that loop as
        # FCN.unwind.K
        match = re.match(r'^(.*)\.unwind\.([0-9]+)$', name)
        if match is None:
            return None
        loop = '{}.{}'.format(match.group(1), match.group(2))

        return self.lookup(loop) or self.lookup_static(loop)

################################################################

class LoopFromJson(Loop):
    """Load cbmc loop table from output of make-loop.

    Given a list of json files containing symbol tables produced by
    make-loop, merge these loop tables into a single loop table.
    """


    def __init__(self, json_files):

        super().__init__(
            [parse.parse_json_file(json_file)[JSON_TAG]['loops']
             for json_file in json_files]
        )

################################################################

class LoopFromCbmcJson(Loop):
    """Load loop table from output of 'cbmc --show-loops --json-ui."""

    def __init__(self, json_files, root):

        super().__init__(
            [load_cbmc_json(json_file, root) for json_file in json_files]
        )

def load_cbmc_json(json_file, root):
    """Load a json file produced by cbmc --show-loops --json-ui."""

    return parse_cbmc_json(parse.parse_json_file(json_file), root)

def parse_cbmc_json(json_data, root):
    """Parse the json output of cbmc --show-loops --json-ui."""

    # Search cbmc output for {"loops": [ LOOP ]}
    loops = [json_map for json_map in json_data if "loops" in json_map]
    if len(loops) != 1:
        raise UserWarning("Expected 1 set of loops in cbmc output, found {}".
                          format(len(loops)))

    # Each LOOP is a dict that gives a loop name and location.
    root = srcloct.abspath(root)
    return {loop['name']:
            srcloct.json_srcloc(loop['sourceLocation'], root)
            for loop in loops[0]["loops"]}

################################################################

class LoopFromCbmcXml(Loop):
    """Load loop table from output of 'cbmc --show-loops --xml-ui."""

    def __init__(self, xml_files, root):

        super().__init__(
            [load_cbmc_xml(xml_file, root) for xml_file in xml_files]
        )

def load_cbmc_xml(xml_file, root):
    """Load an xml file produced by cbmc --show-loops --xml-ui."""

    return parse_cbmc_xml(parse.parse_xml_file(xml_file), root)

def parse_cbmc_xml(xml_data, root):
    """Parse the xml output of cbmc --show-loops --xml-ui."""

    # Each loop element contains loop-id and location elements
    root = srcloct.abspath(root)
    return {loop.find("loop-id").text:
            srcloct.xml_srcloc(loop.find("location"), root)
            for loop in xml_data.iter("loop")}

################################################################

class LoopFromGoto(Loop):
    """Load loop table from a goto binary."""

    def __init__(self, goto, root, cwd=None):

        cmd = ['cbmc', '--show-loops', '--json-ui', goto]
        try:
            super().__init__(
                [parse_cbmc_json(json.loads(runt.run(cmd, cwd=cwd)), root)]
            )
        except subprocess.CalledProcessError as err:
            raise UserWarning(
                'Failed to run {}: {}' .format(cmd, str(err))
            ) from err
        except json.decoder.JSONDecodeError as err:
            raise UserWarning(
                'Failed to parse output of {}: {}'.format(cmd, str(err))
            ) from err

################################################################
# make-loop

# pylint: disable=inconsistent-return-statements

def fail(msg):
    """Log failure and raise exception."""

    logging.info(msg)
    raise UserWarning(msg)

def make_loop(args):
    """The implementation of make-loop"""

    viewer_loop, cbmc_loop, srcdir, goto = args.viewer_loop, None, args.srcdir, args.goto

    if viewer_loop:
        if filet.all_json_files(viewer_loop):
            return LoopFromJson(viewer_loop)
        fail("Expected json files: {}".format(viewer_loop))

    if cbmc_loop and srcdir:
        if filet.all_json_files(cbmc_loop):
            return LoopFromCbmcJson(cbmc_loop, srcdir)
        if filet.all_xml_files(cbmc_loop):
            return LoopFromCbmcXml(cbmc_loop, srcdir)
        fail("Expected json files or xml files, not both: {}"
             .format(cbmc_loop))

    if goto and srcdir:
        return LoopFromGoto(goto, srcdir)

    logging.info("make-loop: nothing to do: need "
                 "--goto and --srcdir, or "
                 "cbmc loop listing results (cbmc --show-loops) and --srcdir, or "
                 "--viewer-loop")
    return Loop()

################################################################
