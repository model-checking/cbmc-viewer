# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""CBMC loop information"""

import json
import logging
import re
import subprocess

import voluptuous

import filet
import srcloct
import parse
import runt
import util

JSON_TAG = 'viewer-loop'

################################################################
# Loop validator

VALID_LOOP = voluptuous.schema_builder.Schema(
    {
        'loops': {
            # loop name -> loop srcloc
            str: srcloct.VALID_SRCLOC
        }
    }
)

################################################################

class Loop:
    """CBMC loop information."""

    def __init__(self, loop_maps):
        """Load CBMC loop map from a lists of loop maps."""

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
        VALID_LOOP(self.__dict__)

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

    def lookup_assertion(self, name):
        """Look up the srcloc for the named loop unwinding assertion."""

        match = re.match(r'^(.*)\.unwind\.([0-9]+)$', name)
        if match is None:
            return None
        loop = '{}.{}'.format(match.group(1), match.group(2))
        return self.lookup(loop)

    def __repr__(self):
        """A dict representation of the loop table."""

        loops = self.__dict__
        VALID_LOOP(loops)
        return loops

    def __str__(self):
        """A string representation of the loop table."""

        return json.dumps({JSON_TAG: self.__repr__()}, indent=2)

################################################################

class LoopFromJson(Loop):
    """Load cbmc loop table from output of make-loop.

    Given a list of json files containing symbol tables produced by
    make-loop, merge these loop tables into a single loop table.
    """


    def __init__(self, json_files):

        super(LoopFromJson, self).__init__(
            [parse.parse_json_file(json_file, fail=True)[JSON_TAG]['loops']
             for json_file in json_files]
        )

################################################################

class LoopFromCbmcJson(Loop):
    """Load loop table from output of 'cbmc --show-loops --json-ui."""

    def __init__(self, json_files, root):

        super(LoopFromCbmcJson, self).__init__(
            [load_cbmc_json(json_file, root) for json_file in json_files]
        )

def load_cbmc_json(json_file, root):
    """Load a json file produced by cbmc --show-loops --json-ui."""

    return parse_cbmc_json(parse.parse_json_file(json_file, fail=True), root)

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

        super(LoopFromCbmcXml, self).__init__(
            [load_cbmc_xml(xml_file, root) for xml_file in xml_files]
        )

def load_cbmc_xml(xml_file, root):
    """Load an xml file produced by cbmc --show-loops --xml-ui."""

    return parse_cbmc_xml(parse.parse_xml_file(xml_file, fail=True), root)

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
            super(LoopFromGoto, self).__init__(
                [parse_cbmc_json(json.loads(runt.run(cmd, cwd=cwd)), root)]
            )
        except subprocess.CalledProcessError as err:
            raise UserWarning('Failed to run {}: {}'
                              .format(cmd, str(err)))
        except json.decoder.JSONDecodeError as err:
            raise UserWarning('Failed to parse output of {}: {}'
                              .format(cmd, str(err)))

################################################################
# make-loop

# pylint: disable=inconsistent-return-statements

def fail(msg):
    """Log failure and raise exception."""

    logging.info(msg)
    raise UserWarning(msg)

def do_make_loop(viewer_loop, cbmc_loop, srcdir, goto):
    """The implementation of make-loop"""

    if viewer_loop:
        if filet.are_json_files(viewer_loop):
            return LoopFromJson(viewer_loop)
        fail("Expected json files: {}".format(viewer_loop))

    if cbmc_loop and srcdir:
        if filet.are_json_files(cbmc_loop):
            return LoopFromCbmcJson(cbmc_loop, srcdir)
        if filet.are_xml_files(cbmc_loop):
            return LoopFromCbmcXml(cbmc_loop, srcdir)
        fail("Expected json files or xml files, not both: {}"
             .format(cbmc_loop))

    if goto and srcdir:
        return LoopFromGoto(goto, srcdir)

    fail("Expected --make-loop, or --srcdir and --goto, "
         "or --srcdir and cbmc loop output.")

################################################################
