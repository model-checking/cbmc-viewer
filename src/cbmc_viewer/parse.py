# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Parsing of xml and json files with limited error handling."""

from pathlib import Path
from xml.etree import ElementTree

import json
import logging
import re

def parse_xml_file(xfile):
    """Parse an xml file."""

    try:
        return ElementTree.parse(xfile)
    except (IOError, ElementTree.ParseError) as err:
        logging.debug("%s", err)
        raise UserWarning(f"Can't load xml file '{xfile}'") from None

def parse_xml_string(xstr):
    """Parse an xml string."""

    try:
        return ElementTree.fromstring(xstr)
    except ElementTree.ParseError as err:
        logging.debug("%s", err)
        raise UserWarning(f"Can't parse xml string '{xstr[:40]}...'") from None

def parse_json_file(jfile, goto_analyzer=False):
    """Parse an json file."""

    try:
        with open(jfile) as data:
            if goto_analyzer:
                return parse_json_string(data.read(), goto_analyzer)
            return json.load(data)
    except (IOError, json.JSONDecodeError, UserWarning) as err:
        logging.debug("%s", err)
        raise UserWarning(f"Can't load json file '{jfile}' in {Path.cwd()}") from None

def parse_json_string(jstr, goto_analyzer=False):
    """Parse a json string."""

    try:
        jstr = clean_up_goto_analyzer(jstr) if goto_analyzer else jstr
        return json.loads(jstr)
    except json.JSONDecodeError as err:
        logging.debug("%s", err)
        raise UserWarning(f"Can't parse json string '{jstr[:40]}...'") from None

def clean_up_goto_analyzer(json_data):
    """Clean up the json output of goto-analyzer."""

    # the json produced by goto-analyzer is preceeded by a block of text
    json_data = re.sub(r'^.*\n\[', '[', json_data, flags=re.DOTALL)
    # the json produced by goto-analyzer sometimes omits line numbers
    json_data = json_data.replace('"first line": ,\n', '"first line": 0,\n')
    json_data = json_data.replace('"last line": \n', '"last line": 0\n')
    return json_data
