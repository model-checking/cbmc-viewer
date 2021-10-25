# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""CBMC property checking results."""

import json
import logging
import re

from voluptuous import Schema, Any
import voluptuous.humanize

from cbmc_viewer import filet
from cbmc_viewer import parse
from cbmc_viewer import propertyt
from cbmc_viewer import util
from cbmc_viewer.util import flatten, choose

JSON_TAG = 'viewer-result'

################################################################
# Validator for property checking results

PROGRAM = 'program'
STATUS = 'status'
WARNING = 'warning'
RESULT = 'results'
PROVER = 'prover'
FAILURE = 'failure'
SUCCESS = 'success'

VALID_RESULT = Schema({
    PROGRAM: Any(str, None), # program version string
    STATUS: [str],           # list of status messages
    WARNING: [str],          # list of warning messages
    RESULT: {
        True : [str],        # list of proved assertions
        False: [str]         # list of failed assertions
    },
    PROVER: Any(FAILURE, SUCCESS, None) # prover status: success or failure
}, required=True)

EMPTY_RESULT = {
    PROGRAM: None,
    STATUS: [],
    WARNING: [],
    RESULT: {
        True: [],
        False: [],
    },
    PROVER: None
}

################################################################
# CBMC property checking results

class Result:
    """CBMC property checking results."""

    def __init__(self, results_list=None):
        """Merge a list of results into a single result.

        Each result is given by the dict representation of a result object.
        """

        results_list = results_list or [EMPTY_RESULT]
        for results in results_list:
            self.validate(results)

        self.program = choose([results[PROGRAM] for results in results_list])
        self.status = flatten([results[STATUS] for results in results_list])
        self.warning = flatten([results[WARNING] for results in results_list])

        success = set(flatten([results[RESULT][True] for results in results_list]))
        failure = set(flatten([results[RESULT][False] for results in results_list]))
        self.results = {
            True: sorted(success.difference(failure), key=propertyt.key),
            False: sorted(failure, key=propertyt.key)
        }

        status = [results[PROVER] for results in results_list] or [None]
        self.prover = None if None in status else FAILURE if FAILURE in status else SUCCESS
        self.validate()

    def __repr__(self):
        """A dict representation of results."""

        self.validate()
        return self.__dict__

    def __str__(self):
        """A string representation of results."""

        return json.dumps({JSON_TAG: self.__repr__()}, indent=2, sort_keys=True)

    def validate(self, results=None):
        """Validate results."""

        return voluptuous.humanize.validate_with_humanized_errors(
            results or self.__dict__, VALID_RESULT
        )

    def dump(self, filename=None, directory=None):
        """Write results to a file or stdout."""

        util.dump(self, filename, directory)

################################################################
# CBMC property checking results loaded from make-result json data

class ResultFromJson(Result):
    """CBMC property checking results loaded from make-result json data"""

    def __init__(self, json_files):
        super().__init__(
            [self.load_results(json_file) for json_file in json_files]
        )

    @staticmethod
    def load_results(json_file):
        """Load CBMC results from json file"""

        blob = parse.parse_json_file(json_file)[JSON_TAG]

        # json uses strings "true" and "false" for True and False keys
        blob[RESULT][True] = blob[RESULT]["true"]
        blob[RESULT][False] = blob[RESULT]["false"]
        del blob[RESULT]["true"]
        del blob[RESULT]["false"]

        return blob

################################################################
# CBMC property checking results loaded from cbmc text output

class ResultFromCbmcText(Result):
    """CBMC property checking results loaded from cbmc text output"""

    def __init__(self, text_files):
        super().__init__(
            [parse_cbmc_text_results(text_file) for text_file in text_files]
        )

################################################################
# CBMC property checking results loaded from cbmc json output

class ResultFromCbmcJson(Result):
    """CBMC property checking results loaded from cbmc json output"""

    def __init__(self, json_files):
        super().__init__(
            [parse_cbmc_json_results(json_file) for json_file in json_files]
        )

################################################################
# CBMC property checking results loaded from cbmc xml output

class ResultFromCbmcXml(Result):
    """CBMC property checking results loaded from CBMC xml output"""

    def __init__(self, xml_files):
        super().__init__(
            [parse_cbmc_xml_results(xml_file) for xml_file in xml_files]
        )

################################################################
# Parse the text output of cbmc property checking into sections
#
# This parsing is required only for text output of cbmc.  The text
# output is just an unstructured sequence of lines with embedded
# section headers.  The json and xml output of cbmc are already
# structured into sections, and sections are easy to find.

LOG_SECTION = 'log'
RESULTS_SECTION = 'results'
TRACES_SECTION = 'traces'
SUMMARY_SECTION = 'summary'

EMPTY_SECTIONS = {
    LOG_SECTION: [],
    RESULTS_SECTION: [],
    TRACES_SECTION: [],
    SUMMARY_SECTION: []
}

RESULTS_SECTION_HEADER = "** Results"
TRACES_SECTION_HEADER = "Trace for"
SUMMARY_SECTION_HEADER = "** " # Caution: summary header is a prefix of results header

def cbmc_text_sections(text_file):
    """Parse the text output of cbmc property checking into sections"""

    sections = EMPTY_SECTIONS
    with open(text_file, encoding='utf-8') as blob:
        # The blob is an iterator that iterates through the lines of
        # the file and throws StopIteration at the end of the file.
        next_line = lambda : next(blob).rstrip()
        try:
            line = next_line()

            # Log section is from here to results section
            while not line.startswith(RESULTS_SECTION_HEADER):
                sections[LOG_SECTION].append(line)
                line = next_line()

            # Results section is from here to traces section or summary section
            # Traces section is optional: generated by `cbmc --trace`
            line = next_line() # skip results header
            while (not line.startswith(TRACES_SECTION_HEADER) and
                   not line.startswith(SUMMARY_SECTION_HEADER)):
                sections[RESULTS_SECTION].append(line)
                line = next_line()

            # Traces section is from here to summary section
            # Traces section is optional: generated by `cbmc --trace`
            if line.startswith(TRACES_SECTION_HEADER):
                while not line.startswith(SUMMARY_SECTION_HEADER):
                    sections[TRACES_SECTION].append(line)
                    line = next_line()

            # Summary section is from here to end of file
            while True:
                sections[SUMMARY_SECTION].append(line)
                line = next_line()
        except StopIteration:
            return sections

################################################################
# Parse cbmc property checking output

def parse_cbmc_text_results(text_file):
    """Parse text output of cbmc property checking"""

    try:
        sections = cbmc_text_sections(text_file)
    except OSError as error:
        raise UserWarning(f"Can't parse {text_file}: {str(error)}") from error

    results = EMPTY_RESULT
    results[PROGRAM] = cbmc_text_program(sections[LOG_SECTION])
    results[STATUS] = cbmc_text_status(sections[LOG_SECTION], sections[SUMMARY_SECTION])
    results[WARNING] = cbmc_text_warnings(sections[LOG_SECTION])
    results[RESULT] = cbmc_text_results(sections[RESULTS_SECTION])
    results[PROVER] = cbmc_text_prover(sections[SUMMARY_SECTION])

    return results

def parse_cbmc_json_results(json_file):
    """Parse json output of cbmc property checking"""

    blob = parse.parse_json_file(json_file)
    if blob is None:
        return EMPTY_RESULT

    results = EMPTY_RESULT
    results[PROGRAM] = cbmc_json_program(blob)
    results[STATUS] = cbmc_json_status(blob)
    results[WARNING] = cbmc_json_warnings(blob)
    results[RESULT] = cbmc_json_results(blob)
    results[PROVER] = cbmc_json_prover(blob)

    return results

def parse_cbmc_xml_results(xml_file):
    """Parse xml output of cbmc property checking"""

    blob = parse.parse_xml_file(xml_file)
    if blob is None:
        return EMPTY_RESULT

    results = EMPTY_RESULT
    results[PROGRAM] = cbmc_xml_program(blob)
    results[STATUS] = cbmc_xml_status(blob)
    results[WARNING] = cbmc_xml_warnings(blob)
    results[RESULT] = cbmc_xml_results(blob)
    results[PROVER] = cbmc_xml_prover(blob)

    return results

# Keys used in cbmc json output

JSON_DESCRIPTION_KEY = 'description'
JSON_MESSAGE_TEXT_KEY = 'messageText'
JSON_MESSAGE_TYPE_KEY = 'messageType'
JSON_PROGRAM_KEY = 'program'
JSON_PROPERTY_KEY = 'property'
JSON_PROVER_STATUS_KEY = 'cProverStatus'
JSON_RESULT_KEY = 'result'
JSON_STATUS_KEY = 'status'

JSON_STATUS_MESSAGE = 'STATUS-MESSAGE'
JSON_SUCCESS = 'SUCCESS'
JSON_WARNING = 'WARNING'

JSON_PROVER_STATUS_SUCCESS = 'success'

# Keys used in cbmc xml output

XML_FAILURE_TAG = 'failure'
XML_GOTO_TRACE_TAG = 'goto_trace'
XML_LOCATION_TAG = 'location'
XML_MESSAGE_TAG = 'message'
XML_MESSAGE_TEXT_TAG = 'text'
XML_PROGRAM_TAG = 'program'
XML_PROVER_STATUS_TAG = 'cprover-status'
XML_RESULT_TAG = 'result'

XML_FAILURE_PROPERTY_ATTR = 'property'
XML_FAILURE_REASON_ATTR = 'reason'
XML_MESSAGE_TYPE_ATTR = 'type'
XML_RESULT_PROPERTY_ATTR = 'property'
XML_RESULT_STATUS_ATTR = 'status'

XML_STATUS_MESSAGE = 'STATUS-MESSAGE'
XML_SUCCESS_STATUS = 'SUCCESS'
XML_WARNING_MESSAGE = 'WARNING'

################################################################
# Find PROGRAM in cbmc property checking output

def cbmc_text_program(log_section):
    """Find program in cbmc text output"""

    for line in log_section:
        if line.startswith('CBMC version'):
            return line
    return None

def cbmc_json_program(blobs):
    """Find program in cbmc json output"""

    for blob in blobs:
        program = blob.get(JSON_PROGRAM_KEY)
        if program:
            return program
    return None

def cbmc_xml_program(blob):
    """Find program in cbmc xml output"""

    program = blob.find(XML_PROGRAM_TAG)
    if program is not None:
        return program.text
    return None

################################################################
# Find STATUS messages in cbmc property checking output

def cbmc_text_status(log_section, summary_section):
    """Find status messages in cbmc text output"""

    status = []
    for line in log_section:
        if line and not line.startswith('**** WARNING:'):
            status.append(line)
    for line in summary_section:
        if line and line.startswith('VERIFICATION '):
            status.append(line)
    return status

def cbmc_json_status(blobs):
    """Find status messages in cbmc json output"""

    status = []
    for blob in blobs:
        kind = blob.get(JSON_MESSAGE_TYPE_KEY)
        text = blob.get(JSON_MESSAGE_TEXT_KEY)
        if kind == JSON_STATUS_MESSAGE:
            status.append(text)
    return status

def cbmc_xml_status(blob):
    """Find status messages in cbmc xml output"""

    status = []
    for msg in blob.iter(XML_MESSAGE_TAG):
        if msg.get(XML_MESSAGE_TYPE_ATTR) == XML_STATUS_MESSAGE:
            status.append(msg.find(XML_MESSAGE_TEXT_TAG).text)
    return status

################################################################
# Find WARNING messages in cbmc property checking output

def cbmc_text_warnings(log_section):
    """Find warning messages in cbmc text output"""

    warnings = []
    for line in log_section:
        if line.startswith('**** WARNING:'):
            warnings.append(line)
    return warnings

def cbmc_json_warnings(blobs):
    """Find warning messages in cbmc json output"""

    warnings = []
    for blob in blobs:
        kind = blob.get(JSON_MESSAGE_TYPE_KEY)
        text = blob.get(JSON_MESSAGE_TEXT_KEY)
        if kind == JSON_WARNING:
            warnings.append(text)
    return warnings

def cbmc_xml_warnings(blob):
    """Find warning messages in cbmc xml output"""

    warnings = []
    for msg in blob.iter(XML_MESSAGE_TAG):
        if msg.get(XML_MESSAGE_TYPE_ATTR) == XML_WARNING_MESSAGE:
            warnings.append(msg.find(XML_MESSAGE_TEXT_TAG).text)
    return warnings

################################################################
# Find RESULTS in cbmc property checking output

EMPTY_RESULT_RESULTS = {True: [], False: []}

def cbmc_text_results(results_section):
    """Find results in cbmc text output"""

    results = EMPTY_RESULT_RESULTS
    for line in results_section:
        # Lines given property checking results have the form
        # [name] srcloc description: SUCCESS|FAILURE
        match = re.match(r'\[([^ ]*)\].*: ((FAILURE)|(SUCCESS))', line)
        if match:
            name, status = match.groups()[:2]
            results[status == 'SUCCESS'].append(name)
    return results

def cbmc_json_results(blobs):
    """Find results in cbmc json output"""

    results = EMPTY_RESULT_RESULTS
    for blob in blobs:
        for result in blob.get(JSON_RESULT_KEY) or []:
            name, status = result[JSON_PROPERTY_KEY], result[JSON_STATUS_KEY]
            results[status == JSON_SUCCESS].append(name)
    return results

def cbmc_xml_results(blob):
    """Find results in cbmc xml output"""

    results = EMPTY_RESULT_RESULTS

    # cbmc normal output produces property checking results for all properties
    for result in blob.iter(XML_RESULT_TAG):
        name = result.get(XML_RESULT_PROPERTY_ATTR)
        status = result.get(XML_RESULT_STATUS_ATTR)
        results[status == XML_SUCCESS_STATUS].append(name)

    # cbmc --stop-on-fail output produces one trace with one failure
    if not (results[True] or results[False]):
        trace = blob.find(XML_GOTO_TRACE_TAG)
        if trace is not None:
            results[False] = [trace.find(XML_FAILURE_TAG).get(XML_FAILURE_PROPERTY_ATTR)]

    return results

################################################################
# Find PROVER status in cbmc property checking output

def cbmc_text_prover(summary_section):
    """Find prover status in cbmc text output"""

    # Infer prover status from the lines 'VERIFICATION SUCCESSFUL' or
    # 'VERIFICATION FAILED' in the summary section.

    # In rare cases, cbmc can solve the constraint problem without
    # invoking the constraint solver, and the string '** X of Y
    # failed` that we use as the summary header is not printed. The
    # string 'VERIFICATION SUCCESSFUL' that we look for in the summary
    # section is absorbed into the log section, and the summary
    # section is empty.

    if not summary_section:
        return SUCCESS

    for line in summary_section:
        if line == 'VERIFICATION FAILED':
            return FAILURE
        if line == 'VERIFICATION SUCCESSFUL':
            return SUCCESS
    return None

def cbmc_json_prover(blobs):
    """Find prover status in cbmc json output"""

    for blob in blobs:
        prover = blob.get(JSON_PROVER_STATUS_KEY)
        if prover:
            return SUCCESS if prover == JSON_PROVER_STATUS_SUCCESS else FAILURE
    return None

def cbmc_xml_prover(blob):
    """Find prover status in cbmc xml output"""

    prover = blob.find(XML_PROVER_STATUS_TAG)
    if prover is not None:
        return SUCCESS if prover.text == XML_SUCCESS_STATUS else FAILURE
    return None

################################################################
# make-result

def fail(msg):
    """Log failure and raise exception."""

    logging.info(msg)
    raise UserWarning(msg)

def make_result(viewer_result, cbmc_result):
    """Implementation of make-result."""

    if viewer_result:
        if filet.all_json_files(viewer_result):
            return ResultFromJson(viewer_result)
        fail("Expected a list of json files: {}".format(viewer_result))

    if cbmc_result:
        if filet.all_text_files(cbmc_result):
            return ResultFromCbmcText(cbmc_result)
        if filet.all_json_files(cbmc_result):
            return ResultFromCbmcJson(cbmc_result)
        if filet.all_xml_files(cbmc_result):
            return ResultFromCbmcXml(cbmc_result)
        fail("Expected a list of text files, json files, or xml files: {}"
             .format(cbmc_result))

    logging.info("make-result: nothing to do: need "
                 "cbmc property checking results or "
                 "--viewer-result")
    return Result()

################################################################
