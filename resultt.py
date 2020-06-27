# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""CBMC property checking results.

The Result module describes the results of CBMC property checking, the
Coverage module describes the results of CBMC coverage checking, and
the Property module describes the properties checked during property
checking.
"""

import re
import json
import logging

import voluptuous
import voluptuous.humanize

import filet
import parse
import propertyt
import util

JSON_TAG = 'viewer-result'

################################################################

PROGRAM = 'program'
STATUS = 'status'
WARNING = 'warning'
RESULT = 'results'
PROVER = 'prover'
FAILURE = 'failure'
SUCCESS = 'success'

################################################################
# Property checking results validator

VALID_RESULT = voluptuous.schema_builder.Schema({
    PROGRAM: str,     # program version information
    STATUS: [str],    # list of status messages
    WARNING: [str],   # list of warning messages
    RESULT: {
        True : [str], # list of proved assertions
        False: [str]  # list of failed assertions
    },
    PROVER: str       # prover status: success or failure
}, required=True)

################################################################
# CBMC property checking results

class Result:
    """CBMC property checking results.

    Given a list of property checking results (dict representations of
    the Result object) merge the list of results into a single set of
    results.
    """

    def __init__(self, results_list):
        map(lambda results: results.validate(), results_list)
        self.program = self.flatten_string_list(
            [results[PROGRAM] for results in results_list]
        )
        self.status = self.flatten_string_list_list(
            [results[STATUS] for results in results_list]
        )
        self.warning = self.flatten_string_list_list(
            [results[WARNING] for results in results_list]
        )
        self.results = self.flatten_results_list(
            [results[RESULT] for results in results_list]
        )
        self.prover = self.flatten_prover_list(
            [results[PROVER] for results in results_list]
        )
        self.validate()

    def __repr__(self):
        """A dict representation of results."""

        results = self.__dict__
        success = sorted(results['results'][True], key=propertyt.key)
        failure = sorted(results['results'][False], key=propertyt.key)
        results['results'][True] = success
        results['results'][False] = failure
        self.validate(results)
        return results

    def __str__(self):
        """A string representation of results."""

        return json.dumps({JSON_TAG: self.__repr__()}, indent=2)

    def validate(self, results=None):
        """Validate results."""

        return voluptuous.humanize.validate_with_humanized_errors(
            results or self.__dict__, VALID_RESULT
        )

    def dump(self, filename=None, directory=None):
        """Write results to a file or stdout."""

        util.dump(self, filename, directory)

    @staticmethod
    def flatten_string_list(string_list):
        """Extract a string from a list of strings (expect a unique string)"""

        if not string_list:
            return None
        if len(string_list) == 1:
            return string_list[0]

        strings = set(string_list)
        strings.discard(None)

        if not strings:
            return None
        if len(strings) == 1:
            return strings.pop()

        logging.info('Expected a unique string (%s), found %s strings',
                     strings.pop(), len(strings))
        return strings.pop()

    @staticmethod
    def flatten_string_list_list(string_list_list):
        """Flatten a list of string lists into a single string list"""

        if not string_list_list:
            return None
        if len(string_list_list) == 1:
            return [elt for elt in string_list_list[0] if elt]

        return [elt
                for string_list in string_list_list if string_list
                for elt in string_list if elt]

    @staticmethod
    def flatten_results_list(results_list):
        """Flatten a list of verfication results into a single list"""

        if not results_list:
            return None
        if len(results_list) == 1:
            return results_list[0]

        # We are assuming assertion names are consistent across proofs
        success = {name
                   for results in results_list
                   for name in results[True]}
        failure = {name
                   for results in results_list
                   for name in results[False]}
        success = success.difference(failure)

        return {True: list(success), False: list(failure)}

    @staticmethod
    def flatten_prover_list(prover_list):
        """Combine a list of prover success/failure results into one result"""

        results = {result.lower() for result in prover_list}
        if FAILURE in results:
            return FAILURE
        if SUCCESS in results:
            return SUCCESS
        raise UserWarning('Expected {} or {} in prover results, '
                          'found {}'.format(SUCCESS, FAILURE, results))

################################################################
# CBMC property checking results from make-result

class ResultFromJson(Result):
    """CBMC property checking results from make-result"""

    def __init__(self, json_files):
        super(ResultFromJson, self).__init__(
            [self.load_results(json_file) for json_file in json_files]
        )

    @staticmethod
    def load_results(json_file):
        """Load CBMC results from json file"""

        data = parse.parse_json_file(json_file)[JSON_TAG]

        # json uses strings "true" and "false" for True and False keys
        data[RESULT][True] = data[RESULT]["true"]
        data[RESULT][False] = data[RESULT]["false"]
        del data[RESULT]["true"]
        del data[RESULT]["false"]

        return data

################################################################
# CBMC property checking results from cbmc text output

class ResultFromCbmcText(Result):
    """CBMC property checking results from CBMC text output"""

    def __init__(self, text_files):
        super(ResultFromCbmcText, self).__init__(
            [self.parse_results(text_file) for text_file in text_files]
        )

    @staticmethod
    def parse_results(textfile):
        """Parse CBMC results in text output"""

        # Using --verbosity 4 omits the program version data in
        # textual output, so default to "CBMC" in case it is missing.
        results = {
            PROGRAM: "CBMC", STATUS: [], WARNING: [],
            RESULT: {True: [], False: []}, PROVER: None
        }

        # TODO: handle cbmc --stop-on-fail text output
        section = None
        with open(textfile) as data:
            for line in data:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('CBMC version'):
                    results[STATUS].append(line)
                    results[PROGRAM] = line
                    continue
                if line.startswith('**** WARNING:'):
                    results[WARNING].append(line)
                    continue
                if line == 'VERIFICATION FAILED':
                    results[STATUS].append(line)
                    results[PROVER] = FAILURE
                    continue
                if line == 'VERIFICATION SUCCESSFUL':
                    results[STATUS].append(line)
                    results[PROVER] = SUCCESS
                    continue
                if line.startswith('** Results:'):
                    section = 'result'
                    continue
                if line.startswith('Trace for '):
                    section = 'trace'
                    # trace module collects traces
                    continue
                if section == 'result':
                    match = re.match(
                        r'\[(.*)\] line [0-9]+ (.*): ((FAILURE)|(SUCCESS))',
                        line)
                    if match:
                        name, _, status = match.groups()[:3]
                        success = status == 'SUCCESS'
                        results[RESULT][success].append(name)
                    continue
                if section == 'trace':
                    # trace module collects traces
                    continue
                else:
                    results[STATUS].append(line)

        return results

################################################################
# CBMC property checking results from cbmc json output

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

class ResultFromCbmcJson(Result):
    """CBMC property checking results from CBMC json output"""

    def __init__(self, json_files):
        super(ResultFromCbmcJson, self).__init__(
            [self.parse_results(json_file) for json_file in json_files]
        )

    @staticmethod
    def parse_results(jsonfile):
        """Parse CBMC results in json output"""

        results = {
            PROGRAM: None, STATUS: [], WARNING: [],
            RESULT: {True: [], False: []}, PROVER: None
        }

        data = parse.parse_json_file(jsonfile)
        if data is None:
            return results

        # TODO: handle cbmc --stop-on-fail json output
        for entry in data:
            if JSON_PROGRAM_KEY in entry:
                results[PROGRAM] = entry[JSON_PROGRAM_KEY]
                continue

            if JSON_MESSAGE_TYPE_KEY in entry:
                kind = entry[JSON_MESSAGE_TYPE_KEY]
                text = entry[JSON_MESSAGE_TEXT_KEY]
                if kind == JSON_STATUS_MESSAGE:
                    results[STATUS].append(text)
                    continue
                if kind == JSON_WARNING:
                    results[WARNING].append(text)
                    continue
                raise UserWarning('Unknown CBMC json message type {}'
                                  .format(kind))

            if JSON_RESULT_KEY in entry:
                for result in entry[JSON_RESULT_KEY]:
                    name = result[JSON_PROPERTY_KEY]
                    success = result[JSON_STATUS_KEY] == JSON_SUCCESS
                    results[RESULT][success].append(name)
                continue

            if JSON_PROVER_STATUS_KEY in entry:
                results[PROVER] = entry[JSON_PROVER_STATUS_KEY]
                continue

            raise UserWarning('Unrecognized CBMC json results data: {}'
                              .format(entry))

        return results

################################################################
# CBMC property checking results from cbmc xml output

XML_FAILURE_TAG = 'failure'
XML_GOTO_TRACE_TAG = 'goto_trace'
XML_MESSAGE_TAG = 'message'
XML_PROGRAM_TAG = 'program'
XML_PROVER_STATUS_TAG = 'cprover-status'
XML_RESULT_TAG = 'result'
XML_MESSAGE_TEXT_TAG = 'text'

XML_FAILURE_REASON_ATTR = 'reason'
XML_MESSAGE_TYPE_ATTR = 'type'
XML_RESULT_PROPERTY_ATTR = 'property'
XML_FAILURE_PROPERTY_ATTR = 'property'
XML_RESULT_STATUS_ATTR = 'status'

XML_STATUS_MESSAGE = 'STATUS-MESSAGE'
XML_WARNING_MESSAGE = 'WARNING'
XML_SUCCESS_STATUS = 'SUCCESS'

class ResultFromCbmcXml(Result):
    """CBMC property checking results from CBMC xml output"""

    def __init__(self, xml_files):
        super(ResultFromCbmcXml, self).__init__(
            [self.parse_results(xml_file) for xml_file in xml_files]
        )

    @staticmethod
    def parse_results(xml_file):
        """Parse CBMC results in xml output"""

        results = {
            PROGRAM: None, STATUS: [], WARNING: [],
            RESULT: {True: [], False: []}, PROVER: None
        }

        xml = parse.parse_xml_file(xml_file)
        if xml is None:
            return results

        line = xml.find(XML_PROGRAM_TAG)
        if line is not None: # Why does "if line:" not work?
            results[PROGRAM] = line.text

        for line in xml.iter(XML_MESSAGE_TAG):
            kind = line.get(XML_MESSAGE_TYPE_ATTR)
            if kind == XML_STATUS_MESSAGE:
                results[STATUS].append(line.find(XML_MESSAGE_TEXT_TAG).text)
                continue
            if kind == XML_WARNING_MESSAGE:
                results[WARNING].append(line.find(XML_MESSAGE_TEXT_TAG).text)
                continue

        # This explicit comparison with None should be redundant, but
        # 'xml.find' is returning an object and 'if xml.find' is
        # returning false.
        if xml.find(XML_RESULT_TAG) is not None:
            # cbmc produced all results as usual
            for line in xml.iter(XML_RESULT_TAG):
                name = line.get(XML_RESULT_PROPERTY_ATTR)
                success = line.get(XML_RESULT_STATUS_ATTR) == XML_SUCCESS_STATUS
                results[RESULT][success].append(name)
        elif xml.find(XML_GOTO_TRACE_TAG) is not None:
            # cbmc produced only a one one after being run with --stop-on-fail
            failure = xml.find(XML_GOTO_TRACE_TAG).find(XML_FAILURE_TAG)
            name = failure.get(XML_FAILURE_PROPERTY_ATTR)
            results[RESULT][False].append(name)

        line = xml.find(XML_PROVER_STATUS_TAG)
        if line is not None: # Why does "if line:" not work?
            results[PROVER] = line.text

        return results

################################################################
# make-result

# pylint: disable=inconsistent-return-statements

def fail(msg):
    """Log failure and raise exception."""

    logging.info(msg)
    raise UserWarning(msg)

def do_make_result(viewer_result, cbmc_result):
    """Implementation of make-result."""

    if viewer_result:
        if filet.all_json_files(viewer_result):
            return ResultFromJson(viewer_result)
        fail("Expected json files: {}".format(viewer_result))

    if cbmc_result:
        if filet.all_text_files(cbmc_result):
            return ResultFromCbmcText(cbmc_result)
        if filet.all_json_files(cbmc_result):
            return ResultFromCbmcJson(cbmc_result)
        if filet.all_xml_files(cbmc_result):
            return ResultFromCbmcXml(cbmc_result)
        fail("Expected text files json files or xml files, not both: {}"
             .format(cbmc_result))

    fail("Expected --viewer-result or cbmc property checking results.")

################################################################
