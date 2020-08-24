# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""CBMC coverage checking results.

The Result module describes the results of CBMC property checking, the
Coverage module describes the results of CBMC coverage checking, and
the Property module describes the properties checked during property
checking.
"""

import enum
import json
import logging
import re

import voluptuous
import voluptuous.humanize

from cbmc_viewer import filet
from cbmc_viewer import parse
from cbmc_viewer import srcloct
from cbmc_viewer import util

JSON_TAG = 'viewer-coverage'

################################################################
# Line coverage status

class Status(enum.Enum):
    """Line coverage status."""

    HIT = 1
    MISSED = 2
    BOTH = 3

    def __repr__(self):
        """A string representation of line coverage"""

        # TODO: a JSONEncoder for Status enums so json.dumps(Status.HIT) works

        if self == Status.HIT:
            return "hit"
        if self == Status.MISSED:
            return "missed"
        if self == Status.BOTH:
            return "both"
        raise UserWarning("Found unknown line coverage status: {}".format(self))

    def __str__(self):
        """A string representation of line coverage"""

        return self.__repr__()

    @classmethod
    def new(cls, status):
        """Decode a string representation of line coverage"""

        # extend function to the identity function on status instances
        if isinstance(status, Status):
            return status

        if status.lower() == "hit":
            return Status.HIT
        if status.lower() == "missed":
            return Status.MISSED
        if status.lower() == "both":
            return Status.BOTH
        raise UserWarning("Found unknown line coverage status: {}"
                          .format(status))

    def combine(self, status):
        """Combine line coverage"""

        # extend function to None
        if status is None:
            return self

        # extend function to strings (raise exception for invalid strings)
        status = Status.new(status)

        if self == status:
            return self
        return Status.BOTH

################################################################
# Line coverage validator

LINES_COVERED = voluptuous.schema_builder.Schema(
    {
        'percentage': float, # lines hit / lines total
        'hit': int,
        'total': int
    }, required=True
)

RAW_COVERAGE_DATA = voluptuous.schema_builder.Schema(
    {   # file name ->
        str: {
            # function name ->
            str: {
                # line number -> coverage status
                int: Status
            }
        }
    }, required=True
)

LINE_COVERAGE = voluptuous.schema_builder.Schema(
    {  # file name ->
        str: {
            # line number -> coverage status
            int: Status
        }
    }, required=True
)

FUNCTION_COVERAGE = voluptuous.schema_builder.Schema(
    {  # file name ->
        str: {
            # function name -> (percent, hit, total)
            str: LINES_COVERED
        }
    }, required=True
)

OVERALL_COVERAGE = voluptuous.schema_builder.Schema(LINES_COVERED)


VALID_COVERAGE = voluptuous.schema_builder.Schema(
    {
        'coverage': RAW_COVERAGE_DATA,
        'line_coverage': LINE_COVERAGE,
        'function_coverage': FUNCTION_COVERAGE,
        'overall_coverage': OVERALL_COVERAGE
    }, required=True
)

################################################################
# Line coverage

class Coverage:
    """CBMC coverage checking results"""

    def __init__(self, coverage_list):
        """Load CBMC coverage data."""

        # TODO: distinguish between coverage of source code and proof code

        self.coverage = merge_coverage_data(coverage_list)
        self.line_coverage = extract_line_coverage(self.coverage)
        self.function_coverage = extract_function_coverage(self.coverage)
        self.overall_coverage = extract_overall_coverage(self.function_coverage)
        self.validate()

    def __repr__(self):
        """A dict representation of line coverage"""

        self.validate()
        return self.__dict__

    def __str__(self):
        """A string representation of line coverage"""

        def serialize(data):
            """Serialize line coverage for the json encoder"""

            if isinstance(data, Status):
                return str(data)
            if isinstance(data, dict):
                return {key: serialize(val) for key, val in data.items()}
            return data

        return json.dumps({JSON_TAG: serialize(self.__repr__())}, indent=2)

    def validate(self):
        """Validate coverage."""

        return voluptuous.humanize.validate_with_humanized_errors(
            self.__dict__, VALID_COVERAGE
        )

    def dump(self, filename=None, directory=None):
        """Write coverage to a file or stdout."""

        util.dump(self, filename, directory)

    def lookup(self, filename, line):
        """Lookup line coverage status."""

        return self.line_coverage.get(filename, {}).get(line)

def merge_coverage_data(coverage_list):
    """Merge sets of coverage data"""

    coverage = {}
    for coverage_data in coverage_list:
        if not coverage_data:
            logging.info("Found coverage data missing: %s", coverage_data)
            continue

        # file name -> function data
        for filename, function_data in coverage_data.items():

            # The source locations produced by srcloct have paths
            # relative to the source root for all files under the
            # root, and have absolute paths for all other files.
            if filename.startswith('/'):
                logging.info("Restricting coverage to files under the source "
                             "root: skipping %s", filename)
                continue

            coverage[filename] = coverage.get(filename, {})
            # function -> line data
            for func, line_data in function_data.items():
                coverage[filename][func] = coverage[filename].get(func, {})
                # line -> coverage status
                for line, status in line_data.items():
                    cov = coverage[filename][func].get(line)
                    cov = Status.new(status).combine(cov)
                    coverage[filename][func][line] = cov

    try:
        RAW_COVERAGE_DATA(coverage)
    except voluptuous.error.Error as error:
        raise UserWarning("Error merging coverage data: {}".format(error))
    return coverage


# line_coverage: file name -> line number -> status
def extract_line_coverage(coverage):
    """Extract line coverage from raw coverage data."""

    line_coverage = {}
    # file name -> function data
    for filename, function_data in coverage.items():
        line_coverage[filename] = {}
        # function -> line data
        for _, line_data in function_data.items():
            # line -> coverage status
            for line, status in line_data.items():
                line_coverage[filename][line] = status
    return line_coverage

# function_coverage: file name -> function name -> (percentage, hit, total)
def extract_function_coverage(coverage):
    """Extract function coverage from raw coverage data."""

    function_coverage = {}
    # file name -> function data
    for filename, function_data in coverage.items():
        function_coverage[filename] = {}
        # function name -> line data
        for function, line_data in function_data.items():
            hit = 0
            total = 0
            # line number -> coverage status
            for _, status in line_data.items():
                hit = hit + 1 if status != Status.MISSED else hit
                total = total + 1
            percentage = float(hit)/float(total) if total else 0.0
            function_coverage[filename][function] = {
                'percentage': percentage,
                'hit': hit,
                'total': total
            }
    return function_coverage

# overall_coverage: (percentage, hit, total)
def extract_overall_coverage(function_coverage):
    """Extract overall coverage from function coverage data."""

    hit = 0
    total = 0
    # file name -> function data
    for _, function_data in function_coverage.items():
        # function name -> coverage data
        for _, lines_covered in function_data.items():
            hit += lines_covered['hit']
            total += lines_covered['total']
    percentage = float(hit)/float(total) if total else 0.0
    return {
        'percentage': percentage,
        'hit': hit,
        'total': total
    }

################################################################
# Coverage from json output of make-coverage

class CoverageFromJson(Coverage):
    # pylint: disable=too-few-public-methods
    """CBMC coverage results from make-coverage"""

    def __init__(self, json_files):
        super(CoverageFromJson, self).__init__(
            [load_json(json_file) for json_file in json_files]
        )

def load_json(json_file):
    """Load json file produced by make-coverage"""

    json_data = parse.parse_json_file(json_file, fail=True)
    if json_data is None:
        logging.info("Found empty json coverage data.")
        return None

    coverage = repair_json(json_data[JSON_TAG]['coverage'])
    try:
        RAW_COVERAGE_DATA(coverage)
    except voluptuous.error.Error as error:
        raise UserWarning("Error loading json coverage data: {}: {}"
                          .format(json_file, error))
    return coverage

def repair_json(coverage):
    """Replace strings with typed values in coverage loaded from json."""

    # Coverage has the type
    #   coverage: file_name -> func_name -> line_num -> HIT/MISSED/BOTH
    # or
    #   proj_data: file -> file_data
    #   file_data: func -> func_data
    #   func_data: line -> status
    # but json represents both line and status as strings

    fix_func = lambda func_data: {int(line_): Status.new(line_data_)
                                  for line_, line_data_ in func_data.items()}
    fix_file = lambda file_data: {func_: fix_func(func_data_)
                                  for func_, func_data_ in file_data.items()}
    fix_proj = lambda proj_data: {file_: fix_file(file_data_)
                                  for file_, file_data_ in proj_data.items()}
    return fix_proj(coverage)

################################################################
# Coverage from json output of cbmc

class CoverageFromCbmcJson(Coverage):
    # pylint: disable=too-few-public-methods
    """CBMC coverage results from cbmc --cover location --json-ui."""

    def __init__(self, json_files, root):
        root = srcloct.abspath(root)
        super(CoverageFromCbmcJson, self).__init__(
            [load_cbmc_json(json_file, root) for json_file in json_files]
        )

def load_cbmc_json(json_file, root):
    """Load json file produced by cbmc --cover location --json-ui."""

    json_data = parse.parse_json_file(json_file, fail=True)
    if not json_data:
        logging.info("Expected coverage data in json file %s, found none",
                     json_file)
        return None

    goal_list = [entry for entry in json_data if 'goals' in entry]
    if len(goal_list) != 1:
        logging.info("Expected 1 block of goal data in json file %s, found %s",
                     json_file, len(goal_list))
        return None
    goals = goal_list[0]

    coverage = {}
    for goal in goals["goals"]:
        description = goal["description"]
        status = goal["status"]
        location = goal["sourceLocation"]
        srcloc = srcloct.json_srcloc(location, root)
        coverage = add_coverage_data(coverage, description, status, srcloc)

    try:
        RAW_COVERAGE_DATA(coverage)
    except voluptuous.error.Error as error:
        raise UserWarning("Error loading cbmc json coverage data: {}: {}"
                          .format(json_file, error))
    return coverage

################################################################
# Coverage from xml output of cbmc

class CoverageFromCbmcXml(Coverage):
    # pylint: disable=too-few-public-methods
    """CBMC coverage results from cbmc --cover location --xml-ui."""

    def __init__(self, xml_files, root):
        root = srcloct.abspath(root)
        super(CoverageFromCbmcXml, self).__init__(
            [load_cbmc_xml(xml_file, root) for xml_file in xml_files]
        )

def load_cbmc_xml(xml_file, root):
    """Load xml file produced by cbmc --cover location --xml-ui."""

    xml = parse.parse_xml_file(xml_file, fail=True)
    if not xml or xml is None:   # Why is 'xml is None' required?
        logging.info("Expected coverage data in xml file %s, found none",
                     xml_file)
        return None

    coverage = {}
    for goal in xml.iter("goal"):
        description = goal.get("description")
        status = goal.get("status")
        location = goal.find("location")
        srcloc = srcloct.xml_srcloc(location, root)
        coverage = add_coverage_data(coverage, description, status, srcloc)

    try:
        RAW_COVERAGE_DATA(coverage)
    except voluptuous.error.Error as error:
        raise UserWarning("Error loading cbmc xml coverage data: {}: {}"
                          .format(xml_file, error))
    return coverage

################################################################
# Parse coverage data

def add_coverage_data(coverage, description, status, srcloc):
    """Add to coverage the coverage data reported for a coverage goal"""

    if not description:
        logging.debug("Expected coverage data, found %s", description)
        return coverage

    hit = parse_coverage_status(status)
    locations = parse_coverage_description(description)
    locations = clean_up_location_names(locations, srcloc)

    for path, func, line in locations:
        coverage = update_coverage(coverage, path, func, line, hit)
    return coverage

def update_coverage(coverage, path, func, line, status):
    """Add to coverage the coverage status of a single line"""

    coverage[path] = coverage.get(path, {})
    coverage[path][func] = coverage[path].get(func, {})
    coverage[path][func][line] = coverage[path][func].get(line, status)
    coverage[path][func][line] = coverage[path][func][line].combine(status)
    return coverage

def clean_up_location_names(locations, srcloc):
    """Clean up file names and functions names in coverage location data"""

    # Use srcloc file names: viewer source location paths are relative
    # to the source root, cbmc source location paths (that appear in
    # the locations extracted from cbmc output) are relative to the
    # working directory.

    # Use location function names: function names appearing in cbmc
    # goal descriptions (and hence in locations) are "cleaner" than
    # function names appearing in cbmc source locations (and hence in
    # viewer source locations).
    # Examples of "dirty" vs "clean" function names are:
    #   inlined functions: function$link1 vs function
    #   intrinsics: __atomic_compare_exchange vs Atomic_CompareAndSwap

    srcloc_file = srcloc['file']
    srcloc_func = srcloc['function']
    srcloc_line = srcloc['line']

    return [(srcloc_file or loc_file,
             loc_func or srcloc_func,
             loc_line or srcloc_line)
            for loc_file, loc_func, loc_line in locations]

################################################################
# Parse the basic block of code in a coverage goal

def parse_coverage_description(string):
    """Parse a coverage description and extract the basic block covered."""

    # The coverage description has the form "block N (lines BASIC_BLOCK)"
    match = re.match(r'block [0-9]+ \(lines (.*)\)', string)
    if not match:
        logging.info("Found unparsable basic block description: %s", string)
        return None

    return parse_basic_block(match.group(1))

def parse_basic_block(basic_block):
    """Parse a basic block of coverage"""

    # The basic block is a sequence of chunks CHUNK1;CHUNK2;CHUNK3
    return [location
            for chunk in basic_block.split(';')
            for location in parse_chunk(chunk)]

def parse_chunk(chunk):
    """Parse a chunk of coverage"""

    # The chunk has the form FILE:FUNCTION:LINES
    filename, function, lines = chunk.split(':')
    return [(filename, function, line) for line in parse_lines(lines)]

def parse_lines(lines):
    """Parse the lines in a chunk of coverage"""

    # groups of lines are separated by commas.
    # a group of lines is either a single line N or a range of lines N-M
    line_list = []
    for line_range in lines.split(','):
        bounds = line_range.split('-')
        if len(bounds) == 1:
            # Add the single line N
            line_list.append(int(bounds[0]))
        else:
            # Add the range of lines N-M = N, N+1, ..., M
            line_list.extend(range(int(bounds[0]), int(bounds[1])+1))

    # don't worry about duplicates in line_list: if a line is included
    # twice it will be set to the same coverage status twice
    return line_list

################################################################
# Parse the hit/miss status in a coverage goal

def parse_coverage_status(status):
    """Parse a coverage status"""

    return Status.HIT if status.upper() == 'SATISFIED' else Status.MISSED

################################################################
# make-coverage

# pylint: disable=inconsistent-return-statements

def fail(msg):
    """Log failure and raise exception."""

    logging.info(msg)
    raise UserWarning(msg)

def do_make_coverage(viewer_coverage, srcdir, cbmc_coverage):
    """The implementation of make-coverage."""

    if viewer_coverage:
        if filet.all_json_files(viewer_coverage):
            return CoverageFromJson(viewer_coverage)
        fail("Expected json files: {}".format(viewer_coverage))

    if cbmc_coverage and srcdir:
        if filet.all_json_files(cbmc_coverage):
            return CoverageFromCbmcJson(cbmc_coverage, srcdir)
        if filet.all_xml_files(cbmc_coverage):
            return CoverageFromCbmcXml(cbmc_coverage, srcdir)
        fail("Expected json files or xml files, not both: {}"
             .format(cbmc_coverage))

    fail("Expected --viewer-coverage or --srcdir and cbmc coverage results.")



################################################################
