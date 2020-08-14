# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""CBMC traces."""

import json
import logging
import re

import voluptuous
import voluptuous.humanize

from cbmc_viewer import filet
from cbmc_viewer import parse
from cbmc_viewer import srcloct
from cbmc_viewer import util

JSON_TAG = 'viewer-trace'

################################################################
# Every trace step has a KIND and a LOCATION and other DETAIL

VALID_FUNCTION_CALL = voluptuous.schema_builder.Schema({
    'kind': 'function-call',
    'location': srcloct.VALID_SRCLOC, # function call
    'hidden': bool,
    'detail' : {
        'name': str,
        'location': srcloct.VALID_SRCLOC # function being called
    }
}, required=True)

VALID_FUNCTION_RETURN = voluptuous.schema_builder.Schema({
    'kind': 'function-return',
    'location': srcloct.VALID_SRCLOC, # function return
    'hidden': bool,
    'detail' : {
        'name': str,
        'location': srcloct.VALID_SRCLOC # function being returned to
    }
}, required=True)

VALID_VARIABLE_ASSIGNMENT = voluptuous.schema_builder.Schema({
    'kind': 'variable-assignment',
    'location': srcloct.VALID_SRCLOC,
    'hidden': bool,
    'detail': {
        'lhs': str,
        'rhs-value': str,
        'rhs-binary': voluptuous.validators.Any(str, None)
    }
}, required=True)

VALID_PARAMETER_ASSIGNMENT = voluptuous.schema_builder.Schema({
    'kind': 'parameter-assignment',
    'location': srcloct.VALID_SRCLOC,
    'hidden': bool,
    'detail': {
        'lhs': str,
        'rhs-value': str,
        'rhs-binary': voluptuous.validators.Any(str, None)
    }
}, required=True)

VALID_FAILURE = voluptuous.schema_builder.Schema({
    'kind': 'failure',
    'location': srcloct.VALID_SRCLOC,
    'hidden': bool,
    'detail': {
        'property': voluptuous.validators.Any(str, None),
        'reason': str
    }
}, required=True)

VALID_ASSUMPTION = voluptuous.schema_builder.Schema({
    'kind': 'assumption',
    'location': srcloct.VALID_SRCLOC,
    'hidden': bool,
    'detail' : {
        "predicate": str
    }
}, required=True)

VALID_STEP = voluptuous.schema_builder.Schema(
    voluptuous.validators.Any(
        VALID_FUNCTION_CALL,
        VALID_FUNCTION_RETURN,
        VALID_VARIABLE_ASSIGNMENT,
        VALID_PARAMETER_ASSIGNMENT,
        VALID_FAILURE,
        VALID_ASSUMPTION
    ), required=True
)

VALID_TRACE = voluptuous.schema_builder.Schema(
    [VALID_STEP],
    required=True
)

VALID_TRACES = voluptuous.schema_builder.Schema({
    'traces': {
        # failed property name -> failure trace
        voluptuous.schema_builder.Optional(str): VALID_TRACE}
}, required=True)

################################################################

class Trace:
    """CBMC error traces.

    Given a list of sets of traces (dict representations of the Trace
    object) merge the traces into a single set of results.
    """

    def __init__(self, trace_lists):

        self.traces = self.merge(trace_lists)
        self.validate()

    def __repr__(self):
        """A dict representation of traces."""

        self.validate()
        return self.__dict__

    def __str__(self):
        """A string representation of traces."""

        return json.dumps({JSON_TAG: self.__repr__()}, indent=2, sort_keys=True)

    def validate(self):
        """Validate tracess."""

        return voluptuous.humanize.validate_with_humanized_errors(
            self.__dict__, VALID_TRACES
        )

    def dump(self, filename=None, directory=None):
        """Write traces to a file or stdout."""

        util.dump(self, filename, directory)

    @staticmethod
    def merge(trace_lists):
        """Merge trace lists."""

        def handle_duplicate(key, val1, val2):
            """Handle different traces for the same assertion."""
            _, _ = val1, val2
            logging.warning("Found duplicate traces for property %s", key)

        traces = util.merge_dicts(trace_lists, handle_duplicate)
        return {name: close_function_stack_frames(trace)
                for name, trace in traces.items()}

################################################################

class TraceFromJson(Trace):
    """Load error traces from output of make-trace."""

    def __init__(self, json_files):
        super(TraceFromJson, self).__init__(
            [load_traces(json_file) for json_file in json_files]
        )

def load_traces(loadfile):
    """Load a trace file."""
    with open(loadfile) as data:
        return json.load(data)[JSON_TAG]

################################################################

class TraceFromCbmcText(Trace):
    """Load error traces from text output of property checking."""

    def __init__(self, text_files, root, wkdir):
        root = srcloct.abspath(root)
        super(TraceFromCbmcText, self).__init__(
            [parse_text_traces(text_file, root, wkdir)
             for text_file in text_files]
        )

def parse_text_traces(textfile, root=None, wkdir=None):
    """Parse a set of text traces."""

    with open(textfile) as data:
        lines = '\n'.join(data.read().splitlines())
        blocks = re.split(r'\n\n+', lines)

    traces = {}

    name = None
    trace = []
    in_trace = False
    for block in blocks:
        if block.startswith('Trace for'):
            if name:
                traces[name] = trace
                name = None
                trace = []
            name = block.split()[-1][:-1]
            in_trace = True
            continue
        if not in_trace:
            continue
        if block.startswith('State'):
            trace.append(parse_text_state(block, root, wkdir))
            continue
        if block.startswith('Assumption'):
            trace.append(parse_text_assumption(block, root, wkdir))
            continue
        if block.startswith('Violated property'):
            trace.append(parse_text_failure(block, root, wkdir))
            continue
        if block.startswith('** '):
            if name:
                traces[name] = trace
            break
        raise UserWarning("Unknown block: {}".format(block))

    return traces

def parse_text_assignment(string):
    """Parse an assignment in a text trace."""

    # trailing binary expression (exp) may be integer, struct, or unknown ?
    match = re.match(r'([^=]+)=(.+) \(([?{},01 ]+)\)', string.strip())
    if match:
        return list(match.groups()[:3])
    match = re.match('([^=]+)=(.+)', string.strip())
    if match:
        return list(match.groups()[:2]) + [None]
    raise UserWarning("Can't parse assignment: {}".format(string))

def parse_text_state(block, root=None, wkdir=None):
    """Parse the state block in a text trace."""

    lines = block.splitlines()
    srcloc = srcloct.text_srcloc(lines[0], wkdir, root)
    # assignment may be split over remaining lines in block
    lhs, rhs_value, rhs_binary = parse_text_assignment(' '.join(lines[2:]))
    return {
        'kind': 'variable-assignment',
        'location': srcloc,
        'hidden': False,
        'detail': {
            'lhs': lhs,
            'rhs-value': rhs_value,
            'rhs-binary': rhs_binary
        }
    }

def parse_text_assumption(block, root=None, wkdir=None):
    """Parse an assumption in a text trace."""

    lines = block.splitlines()
    srcloc = srcloct.text_srcloc(lines[1], wkdir, root)
    return {
        'kind': 'assumption',
        'location': srcloc,
        'hidden': False,
        'detail': {
            'predicate': lines[2].strip()
        }
    }

def parse_text_failure(block, root=None, wkdir=None):
    """Parse a failure in a text trace."""

    lines = block.splitlines()
    srcloc = srcloct.text_srcloc(lines[1], wkdir, root)
    return {
        'kind': 'failure',
        'location': srcloc,
        'hidden': False,
        'detail': {
            'property': None,
            'reason': lines[2].strip()
        }
    }

################################################################

class TraceFromCbmcXml(Trace):
    """Load error traces from xml output of property checking."""

    def __init__(self, xml_files, root):
        root = srcloct.abspath(root)
        super(TraceFromCbmcXml, self).__init__(
            [parse_xml_traces(xml_file, root) for xml_file in xml_files]
        )

def parse_xml_traces(xmlfile, root=None):
    """Parse a set of xml traces."""

    xml = parse.parse_xml_file(xmlfile)
    if xml is None:
        return {}


    traces = {}

    # cbmc produced all traces as usual
    if xml.find('result') is not None:
        for line in xml.iter('result'):
            name, status = line.get('property'), line.get('status')
            if status == 'SUCCESS':
                continue
            traces[name] = parse_xml_trace(line.find('goto_trace'), root)
        return traces

    # cbmc produced only a one trace after being run with --stop-on-fail
    goto_trace = xml.find('goto_trace')
    if goto_trace is not None:
        failure = goto_trace.find('failure')
        name = failure.get('property') if failure else 'Unknown property'
        traces[name] = parse_xml_trace(goto_trace, root)
        return traces

    # cbmc produced no traces
    return traces

def parse_xml_trace(steps, root=None):
    """Parse a single xml trace."""

    trace = [parse_xml_step(step, root) for step in steps]
    return [step for step in trace if step is not None]

def parse_xml_step(step, root=None):
    """Parse a step in an xml trace."""

    if step.get('hidden') == 'true':
        # Skip hidden steps, but retain function call/return pairs
        if step.tag not in ['function_call', 'function_return']:
            return None

    kind = step.tag
    parser = (parse_xml_failure if kind == 'failure' else
              parse_xml_assignment if kind == 'assignment' else
              parse_xml_function_call if kind == 'function_call' else
              parse_xml_function_return if kind == 'function_return' else
              parse_xml_location_only if kind == 'location-only' else None)

    if parser is None:
        logging.warning('Skipping step type: %s', kind)
        return None

    parsed_step = parser(step, root)
    if parsed_step:
        parsed_step['hidden'] = bool(step.get('hidden'))
    return parsed_step

def parse_xml_failure(step, root=None):
    """Parse a failure step in an xml trace."""

    return {
        'kind': 'failure',
        'location': srcloct.xml_srcloc(
            step.find('location'), root
        ),
        'detail': {
            'property': step.get('property'),
            'reason': step.get('reason')
        }
    }

def parse_xml_assignment(step, root=None):
    """Parse an assignment step in an xml trace."""

    akind = step.get('assignment_type')
    kind = ('variable-assignment' if akind == 'state' else
            'parameter-assignment' if akind == 'actual_parameter' else None)
    if kind is None:
        raise UserWarning("Unknown xml assignment type: {}".format(akind))

    return {
        'kind': kind,
        'location': srcloct.xml_srcloc(
            step.find('location'), root
        ),
        'detail': {
            'lhs': step.find('full_lhs').text,
            'rhs-value': step.find('full_lhs_value').text,
            'rhs-binary': None
        }
    }

def parse_xml_function_call(step, root=None):
    """Parse a function call step in an xml trace."""

    return {
        'kind': 'function-call',
        'location': srcloct.xml_srcloc(
            step.find('location'), root
        ),
        'detail': {
            'name': step.find('function').get('display_name'),
            'location': srcloct.xml_srcloc(
                step.find('function').find('location'), root
            )
        }
    }

def parse_xml_function_return(step, root=None):
    """Parse a function return step in an xml trace."""

    return {
        'kind': 'function-return',
        'location': srcloct.xml_srcloc(
            step.find('location'), root
        ),
        'detail': {
            'name': step.find('function').get('display_name'),
            'location': srcloct.xml_srcloc(
                step.find('function').find('location'), root
            )
        }
    }

def parse_xml_location_only(step, root=None):
    """Parse (ignore) a location-only step in an xml trace."""

    _ = step
    _ = root

################################################################

class TraceFromCbmcJson(Trace):
    """Load error traces from json output of property checking."""

    def __init__(self, json_files, root):
        root = srcloct.abspath(root)
        super(TraceFromCbmcJson, self).__init__(
            [parse_json_traces(json_file, root) for json_file in json_files]
        )

def parse_json_traces(jsonfile, root=None):
    """Parse a set of json traces."""

    data = parse.parse_json_file(jsonfile)
    if data is None:
        return {}

    results = [entry['result'] for entry in data if 'result' in entry][0]
    traces = {result['property']: parse_json_trace(result['trace'], root)
              for result in results if 'trace' in result}
    return traces

def parse_json_trace(steps, root=None):
    """Parse a single of json trace."""

    trace = [parse_json_step(step, root) for step in steps]
    return [step for step in trace if step is not None]

def parse_json_step(step, root=None):
    """Parse a step of a json trace."""

    if step['hidden']:
        # Skip hidden steps, but retain function call/return pairs
        if step['stepType'] not in ['function-call', 'function-return']:
            return None

    kind = step['stepType']
    parser = (parse_json_failure if kind == 'failure' else
              parse_json_assignment if kind == 'assignment' else
              parse_json_function_call if kind == 'function-call' else
              parse_json_function_return if kind == 'function-return' else
              parse_json_location_only if kind == 'location-only' else None)
    if parser is None:
        raise UserWarning("Unknown json step type: {}".format(kind))

    parsed_step = parser(step, root)
    if parsed_step:
        parsed_step['hidden'] = bool(step['hidden'])
    return parsed_step

def parse_json_failure(step, root=None):
    """Parse a failure step of a json trace."""

    return {
        'kind': 'failure',
        'location': srcloct.json_srcloc(
            step.get('sourceLocation'), root
        ),
        'detail': {
            'property': step.get('property'),
            'reason': step.get('reason')
        }
    }

def parse_json_assignment(step, root=None):
    """Parse an assignment step of a json trace."""

    akind = step.get('assignmentType')
    kind = ('variable-assignment' if akind == 'variable' else
            'parameter-assignment' if akind == 'actual-parameter' else None)
    if kind is None:
        raise UserWarning("Unknown json assignment type: {}".format(akind))

    # &v is represented as {name: pointer, data: v}
    # NULL is represented as {name: pointer, data:{(basetype *)NULL)}
    data = step['value'].get('data')
    if step['value'].get('name') == 'pointer' and data and 'NULL' not in data:
        data = '&{}'.format(data)

    return {
        'kind': kind,
        'location': srcloct.json_srcloc(
            step.get('sourceLocation'), root
        ),
        'detail': {
            'lhs': step['lhs'],
            'rhs-value': data or json.dumps(step['value']),
            'rhs-binary': binary_as_bytes(step['value'].get('binary'))
        }
    }

def parse_json_function_call(step, root=None):
    """Parse a function call step of a json trace."""

    return {
        'kind': 'function-call',
        'location': srcloct.json_srcloc(
            step.get('sourceLocation'), root
        ),
        'detail': {
            'name': step['function']['displayName'],
            'location': srcloct.json_srcloc(
                step['function']['sourceLocation'], root
            )
        }
    }

def parse_json_function_return(step, root=None):
    """Parse a function return step of a json trace."""

    return {
        'kind': 'function-return',
        'location': srcloct.json_srcloc(
            step.get('sourceLocation'), root
        ),
        'detail': {
            'name': step['function']['displayName'],
            'location': srcloct.json_srcloc(
                step['function']['sourceLocation'], root
            )
        }
    }

def parse_json_location_only(step, root=None):
    """Parse (ignore) a location-only step of a json trace."""

    _ = step
    _ = root

def binary_as_bytes(binary):
    """Reformat binary string as a sequence of bytes."""

    if not binary:
        return binary
    bits = re.sub(r'\s', '', binary)
    bites = re.findall('[01]{8}', bits)
    if bits != ''.join(bites):
        return binary
    return ' '.join(bites)

################################################################

def close_function_stack_frames(trace):
    """Append function-return steps missing from end of a trace.

    The json and xml traces from cbmc include function-call
    and function-return steps, but each error trace ends with
    a failure and omits the function returns for the function
    calls remaining on the call stack.  This appends these
    missing function returns to the end of the trace so that
    all function calls are properly nested and bracketed with
    call/return steps."""

    stack = []

    def push_stack(stack, elt):
        stack.append(elt)
        return stack

    def pop_stack(stack):
        assert stack
        return stack[-1], stack[:-1]

    location = None
    for step in trace:
        kind = step['kind']
        location = step['location']
        callee_name = step.get('detail', {}).get('name')
        callee_location = step.get('detail', {}).get('location')

        if kind == 'function-call':
            stack = push_stack(stack, (callee_name, callee_location))
            continue

        if kind == 'function-return':
            pair, stack = pop_stack(stack)
            callee_name_, _ = pair
            if callee_name != callee_name_:
                raise UserWarning('Function call-return mismatch: {} {}'
                                  .format(callee_name, callee_name_))
            continue

    stack.reverse()
    for callee_name, callee_location in stack:
        function_return = {
            "detail": {
                "location": callee_location,
                "name": callee_name
            },
            "kind": "function-return",
            "location": location,
            "hidden": True # TODO: should match corresponding call
        }
        trace.append(function_return)

    return trace

################################################################
# make-trace

# pylint: disable=inconsistent-return-statements

def fail(msg):
    """Log failure and raise exception."""

    logging.info(msg)
    raise UserWarning(msg)

def do_make_trace(viewer_trace, cbmc_trace, srcdir, wkdir):
    """Implementation of make-trace"""

    if viewer_trace:
        if filet.all_json_files(viewer_trace):
            return TraceFromJson(viewer_trace)
        fail("Expected json files: {}".format(viewer_trace))

    if cbmc_trace and srcdir:
        if filet.all_text_files(cbmc_trace):
            if wkdir:
                return TraceFromCbmcText(cbmc_trace, srcdir, wkdir)
            fail("Expected --srcdir, --wkdir, and cbmc trace output.")
        if filet.all_json_files(cbmc_trace):
            return TraceFromCbmcJson(cbmc_trace, srcdir)
        if filet.all_xml_files(cbmc_trace):
            return TraceFromCbmcXml(cbmc_trace, srcdir)
        fail("Expected json files or xml files, not both: {}"
             .format(cbmc_trace))

    fail("Expected --make-trace or --srcdir, --wkdir, and "
         "cbmc trace output.")

################################################################
