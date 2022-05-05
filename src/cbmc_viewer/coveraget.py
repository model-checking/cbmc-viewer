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
        raise UserWarning(f"Found unknown line coverage status: {self}")

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
        raise UserWarning(f"Found unknown line coverage status: {status}")

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

LINES_COVERED = voluptuous.Schema(
    {
        'percentage': float, # lines hit / lines total
        'hit': int,
        'total': int
    }, required=True
)

RAW_COVERAGE_DATA = voluptuous.Schema(
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

LINE_COVERAGE = voluptuous.Schema(
    {  # file name ->
        str: {
            # line number -> coverage status
            int: Status
        }
    }, required=True
)

FUNCTION_COVERAGE = voluptuous.Schema(
    {  # file name ->
        str: {
            # function name -> (percent, hit, total)
            str: LINES_COVERED
        }
    }, required=True
)

OVERALL_COVERAGE = voluptuous.Schema(LINES_COVERED)


VALID_COVERAGE = voluptuous.Schema(
    {
        'coverage': voluptuous.Any(RAW_COVERAGE_DATA, {}),
        'line_coverage': voluptuous.Any(LINE_COVERAGE, {}),
        'function_coverage': voluptuous.Any(FUNCTION_COVERAGE, {}),
        'overall_coverage': voluptuous.Any(OVERALL_COVERAGE, {})
    }, required=True
)

################################################################
# Line coverage

class Coverage:
    """CBMC coverage checking results"""

    def __init__(self, coverage_list=None):
        """Load CBMC coverage data."""

        coverage_list = coverage_list or []

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

        return json.dumps({JSON_TAG: serialize(self.__repr__())}, indent=2,
                          sort_keys=True)

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
        coverage and RAW_COVERAGE_DATA(coverage)
    except voluptuous.Error as error:
        raise UserWarning(f"Error merging coverage data: {error}") from error
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

    if not function_coverage:
        return {}

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
        super().__init__(
            [load_json(json_file) for json_file in json_files]
        )

def load_json(json_file):
    """Load json file produced by make-coverage"""

    json_data = parse.parse_json_file(json_file)
    if not json_data:
        raise UserWarning(f"Failed to load json coverage data: {json_file}")

    coverage = repair_json(json_data[JSON_TAG]['coverage'])
    try:
        RAW_COVERAGE_DATA(coverage)
    except voluptuous.Error as error:
        raise UserWarning(f"Invalid json coverage data: {json_file}: {error}") from error
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
        super().__init__(
            [load_cbmc_json(json_file, root) for json_file in json_files]
        )

def load_cbmc_json(json_file, root):
    """Load json file produced by cbmc --cover location --json-ui."""

    json_data = parse.parse_json_file(json_file)
    if not json_data:
        raise UserWarning(f"Failed to load json coverage data: {json_file}")

    try:
        goals_list = [entry for entry in json_data if 'goals' in entry]
        assert len(goals_list) == 1
        goals = goals_list[0]['goals']
    except AssertionError as error:
        raise UserWarning(
            f"Failed to locate coverage goals in json coverage data: {json_file}") from error

    coverage = {}
    for goal in goals:
        lines = (parse_basicBlockLines(goal.get("basicBlockLines")) or
                 parse_description(goal.get("description")))
        status = goal["status"]
        wkdir = srcloct.json_srcloc_wkdir(goal["sourceLocation"])
        coverage = add_coverage_data(coverage, lines, status, wkdir, root)

    try:
        RAW_COVERAGE_DATA(coverage)
    except voluptuous.Error as error:
        raise UserWarning(f"Invalid json coverage data: {json_file}: {error}") from error
    return coverage

################################################################
# Coverage from xml output of cbmc

class CoverageFromCbmcXml(Coverage):
    # pylint: disable=too-few-public-methods
    """CBMC coverage results from cbmc --cover location --xml-ui."""

    def __init__(self, xml_files, root):
        root = srcloct.abspath(root)
        super().__init__(
            [load_cbmc_xml(xml_file, root) for xml_file in xml_files]
        )

def load_cbmc_xml(xml_file, root):
    """Load xml file produced by cbmc --cover location --xml-ui."""

    xml = parse.parse_xml_file(xml_file)
    if not xml or xml is None:   # Why is 'xml is None' required?
        raise UserWarning(f"Failed to load xml coverage data: {xml_file}")

    coverage = {}
    for goal in xml.iter("goal"):
        lines = (parse_basic_block_lines(goal.find("basic_block_lines")) or
                 parse_description(goal.get("description")))
        status = goal.get("status")
        wkdir = srcloct.xml_srcloc_wkdir(goal.find("location"))
        coverage = add_coverage_data(coverage, lines, status, wkdir, root)

    try:
        RAW_COVERAGE_DATA(coverage)
    except voluptuous.Error as error:
        raise UserWarning(f"Invalid xml coverage data: {xml_file}: {error}") from error
    return coverage

################################################################
# Parse coverage data

def add_coverage_data(coverage, lines, status, wkdir, root):
    """Add to coverage the coverage data reported for a coverage goal"""

    # Warning: What follows assumes that all relative paths appearing
    # in a coverage goal's list of source lines are relative to the
    # same working directory (the working directory in the coverage
    # goal's source location).  This is probably true.  A project can
    # avoid this issue altogether, however, by invoking goto-cc on
    # absolute paths, ensuring that coverage descriptions contain only
    # absolute paths and no relative paths.

    hit = parse_coverage_status(status)
    lines = relative_locations(lines, wkdir, root)

    for path, func, line in lines:
        coverage = update_coverage(coverage, path, func, line, hit)
    return coverage

def relative_locations(locations, wkdir, root):
    """Replace locations with locations relative to the source root."""

    # Warning: Some goto program transformations currently use a
    # documentation string as a file name in source locations.  The
    # result is a source location that has no valid relative form.  We
    # ignore them when generating coverage data.

    def relative_location(loc_file, loc_func, loc_line):
        """The source location relative to the source root."""
        try:
            return (
                srcloct.make_relative_path(loc_file, root, wkdir),
                loc_func,
                loc_line
            )
        except AssertionError: # raised by make_relative_path
            logging.debug(
                "Ignoring an invalid source location in coverage data:"
                " {file: %s, function: %s, line: %s}",
                loc_file, loc_func, loc_line
            )
            return None

    locations = [relative_location(*loc) for loc in locations]
    locations = [loc for loc in locations if loc is not None]
    return locations

def update_coverage(coverage, path, func, line, status):
    """Add to coverage the coverage status of a single line"""

    coverage[path] = coverage.get(path, {})
    coverage[path][func] = coverage[path].get(func, {})
    coverage[path][func][line] = coverage[path][func].get(line, status)
    coverage[path][func][line] = coverage[path][func][line].combine(status)
    return coverage

################################################################
# Extract the source lines contributing to a coverage goal's basic block
#
# Each coverage goal is a basic block in a goto program. Each
# instruction in a basic block has a source location identifying the
# source line that generated the instruction.
#
# CBMC encodes these source lines in the text of the goal description.
# Later versions of CBMC also encode these source lines a xml or json
# subelements of the goal in CBMC's xml or json coverage output.

def parse_lines(string):
    """Extract line numbers from the string encoding of line numbers used in coverage output"""

    # string is an encoding of a set of line numbers like
    #   "1,3,6" -> {1, 3, 6}
    #   "1-3,6,20-32" -> {1, 2, 3, 6, 20, 21, 22}

    lines = set()
    for group in string.split(','):
        bounds = group.split('-')
        if len(bounds) == 1:
            lines.add(int(bounds[0]))
        elif len(bounds) == 2:
            lines.update(range(int(bounds[0]), int(bounds[1])+1))
        else:
            raise UserWarning(f"Unexpected encoding of line numbers: {string}")
    return sorted(lines)

def parse_description(description):
    """Extract basic block source lines from a coverage goal's textual description"""

    try:
        # description is "block N (lines BASIC_BLOCK)"
        basic_block = re.match(r'block [0-9]+ \(lines (.*)\)', description).group(1)

        # basic_block is
        #   chunk1;chunk2;chunk3
        # each chunk is
        #   test.c:foo:3,6-10
        # each function name foo from rust may include embedded semicolons like
        #   main::foo
        lines = [(fyle, func, line)
                 for chunk in basic_block.split(';')
                 for fyle, func_lines in [chunk.split(':', 1)]  # fyle:func:lines -> fyle,func:lines
                 for func, lines in [func_lines.rsplit(':', 1)] # func:lines -> func,lines
                 for line in parse_lines(lines)]
        assert all(fyle and func and line for fyle, func, line in lines)
        return lines
    except (AttributeError, ValueError, AssertionError) as error:
        # AttributeError after match(): 'NoneType' object has no attribute 'group'
        # ValueError after after split()/rsplit(): not enough values to unpack
        # ValueError in parse_lines(): invalid literal for int()
        raise UserWarning(f'Unexpected coverage goal description: "{description}"') from error

def parse_basic_block_lines(basic_block_lines):
    """Extract basic block source lines from a coverage goal's xml subelement"""

    if basic_block_lines is None:
        return []

    try:
        # basic_block_lines is xml
        #   <basic_block_lines>
        #     <line file="test.c" function="foo">3,6-10</line>
        #     ...
        #   </basic_block_lines>
        lines = [(fyle, func, line)
                 for bbl in basic_block_lines.iter("line")
                 for fyle, func, lines in [(bbl.get("file"), bbl.get("function"), bbl.text)]
                 for line in parse_lines(lines)]
        assert all(fyle and func and line for fyle, func, line in lines)
        return lines
    except (ValueError, AssertionError) as error:
        # ValueError in parse_lines(): invalid literal for int()
        raise UserWarning(f'Unexpected coverage goal xml data: "{basic_block_lines}"') from error

def parse_basicBlockLines(basicBlockLines): # pylint: disable=invalid-name
    """Extract basic block source lines from a coverage goal's json data"""

    if basicBlockLines is None:
        return []

    try:
        # basicBlockLines is json
        #   "basicBlockLines": {
        #     "test.c": {
        #       "main": "16,17"
        #     }
        #   }
        lines = [(fyle, func, line)
                 for fyle, fyle_data in basicBlockLines.items()
                 for func, lines in fyle_data.items()
                 for line in parse_lines(lines)]
        assert all(fyle and func and line for fyle, func, line in lines)
        return lines
    except (ValueError, AssertionError) as error:
        # ValueError in parse_lines(): invalid literal for int()
        raise UserWarning(f'Unexpected coverage goal json data: "{basicBlockLines}"') from error

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

def make_coverage(args):
    """The implementation of make-coverage."""

    viewer_coverage, srcdir, cbmc_coverage = args.viewer_coverage, args.srcdir, args.coverage

    if viewer_coverage:
        if filet.all_json_files(viewer_coverage):
            return CoverageFromJson(viewer_coverage)
        fail(f"Expected json files: {viewer_coverage}")

    if cbmc_coverage and srcdir:
        if filet.all_json_files(cbmc_coverage):
            return CoverageFromCbmcJson(cbmc_coverage, srcdir)
        if filet.all_xml_files(cbmc_coverage):
            return CoverageFromCbmcXml(cbmc_coverage, srcdir)
        fail(f"Expected json files or xml files, not both: {cbmc_coverage}")

    logging.info("make-coverage: nothing to do: need "
                 "cbmc coverage checking results and --srcdir or "
                 "--viewer-coverage")
    return Coverage()

def make_and_save_coverage(args, path=None):
    """Make coverage object and write to file or stdout"""

    obj = make_coverage(args)
    util.save(obj, path)
    return obj

################################################################
