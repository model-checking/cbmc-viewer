# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Parsing of xml and json files with limited error handling."""

from pathlib import Path
from xml.etree import ElementTree

import json
import logging

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

def parse_json_file(jfile):
    """Parse an json file."""

    try:
        with open(jfile, encoding='utf-8') as data:
            return json.load(data)
    except (IOError, json.JSONDecodeError) as err:
        logging.debug("%s", err)
        raise UserWarning(f"Can't load json file '{jfile}' in {Path.cwd()}") from None

def parse_json_string(jstr):
    """Parse a json string."""

    try:
        return json.loads(jstr)
    except json.JSONDecodeError as err:
        logging.debug("%s", err)
        raise UserWarning(f"Can't parse json string '{jstr[:40]}...'") from None
