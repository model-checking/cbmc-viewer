# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Parsing of xml and json files with limited error handling."""

from xml.etree import ElementTree

import json
import logging
import re

def parse_xml_file(xfile, fail=False):
    """Open and parse an xml file."""

    try:
        with open(xfile) as data:
            return parse_xml_string(data.read(), xfile, fail)
    except IOError as err:
        message = "Can't open xml file {}: {}".format(xfile, err.strerror)
        logging.info(message)
        if fail:
            raise UserWarning(message) from None
    return None

def parse_xml_string(xstr, xfile=None, fail=False):
    """Parse an xml string."""

    try:
        return ElementTree.fromstring(xstr)
    except ElementTree.ParseError as err:
        if xfile:
            message = "Can't parse xml file {}: string {}...: {}".format(
                xfile, xstr[:40], str(err)
            )
        else:
            message = "Can't parse xml string {}...: {}".format(
                xstr[:40], str(err)
            )
        logging.info(message)
        if fail:
            raise UserWarning(message) from None
    return None

def parse_json_file(jfile, fail=False, goto_analyzer=False):
    """Open and parse an json file."""

    try:
        with open(jfile) as data:
            return parse_json_string(data.read(), jfile, fail, goto_analyzer)
    except IOError as err:
        message = "Can't open json file {}: {}".format(jfile, err.strerror)
        logging.info(message)
        if fail:
            raise UserWarning(message) from None
    return None

def parse_json_string(jstr, jfile=None, fail=False, goto_analyzer=False):
    """Parse an json string."""

    try:
        jstr = clean_up_goto_analyzer(jstr) if goto_analyzer else jstr
        return json.loads(jstr)
    except json.JSONDecodeError as err:
        if jfile:
            message = "Can't parse json file {}: string {}...: {}".format(
                jfile, jstr[:40], str(err)
            )
        else:
            message = "Can't parse json string {}...: {}".format(
                jstr[:40], str(err)
            )
        logging.info(message)
        if fail:
            raise UserWarning(message) from None

    return None

def clean_up_goto_analyzer(json_data):
    """Clean up the json output of goto-analyzer."""

    # the json produced by goto-analyzer is preceeded by a block of text
    json_data = re.sub(r'^.*\n\[', '[', json_data, flags=re.DOTALL)
    # the json produced by goto-analyzer sometimes omits line numbers
    json_data = json_data.replace('"first line": ,\n', '"first line": 0,\n')
    json_data = json_data.replace('"last line": \n', '"last line": 0\n')
    return json_data
