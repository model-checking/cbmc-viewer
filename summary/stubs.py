#!/usr/bin/env python3

"""List stubbed functions and missing functions in a set of CBMC proofs.

    This script scans the json files produced by cbmc-viewer for a set
    of proofs and constructs for each proof three lists:

    * stubbed: the list of stubbed functions used in the proof (those
      functions defined in code outside the project code itself and under
      the cbmc directory in most proof projects),

    * removed: the list of undefined functions removed by the proof author
      (and listed as as "expected-missing-functions" in the cbmc-viewer
      configuration file cbmc-viewer.json), and

    * missing: the list of undefined functions that are simply missing
      from the proof.

    All of the needed data is in the files viewer-result.json (listing the
    undefined functions in the proof), viewer-reachable.json (list the
    reachable functions in the proof), and cbmc-viewer.json (listing the
    known undefined functions).  The script requires some location
    information (eg, the paths to the json files) that can be provided
    with command line flags, but the script tries to guess this location
    information when it is omitted from the command line.  You can view
    the guesses made with --verbose if the script seems to have guessed
    wrong.

    NOTE: All of this information we need is in the goto binary
    itself, but 'goto-analyzer --reachable-functions' does not include
    undefined functions in the list of reachable functions.
"""


import re
import argparse
import json
import logging
import os
import subprocess
import sys

################################################################
# Command line parser

def create_parser():
    desc = "Summarize the stubs and undefined functions used in a proof."
    args = [
        {
            "flag": "--proof",
            "nargs": "*",
            "help": """
            A list of proof names. A proof name is interpreted as a
            relative path from PROOFDIR to a directory containing a proof
            (see --proofdir PROOFDIR).
            By default, if PROOF is not specified, use all proofs
            discovered under PROOFDIR. """
        },
        {
            "flag": "--srcdir",
            "help": """
            The root of the source tree.   SRCDIR is used only to
            guess CBMCPATH if it is not specified (see
            --cbmcpath CBMCPATH.) By default, if SRCDIR is not specified,
            look for the Makefile in a proof directory and use the
            argument to --srcdir used in the invocation of cbmc-viewer
            by that Makefile.
            """
        },
        {
            "flag": "--proofdir",
            "default": '.',
            "help": """
            The root of the proof tree.  PROOFDIR is used only to
            compute the full path to a proof directory. A proof name
            is interpreted as a relative path from PROOFDIR to a
            directory containing a proof, so PROOFDIR can by any
            directory containing a proof. By default,
            PROOFDIR is the current directory. (Default: %(default)s)
            """
        },
        {
            "flag": "--cbmcpath",
            "help": """
            The relative path from the source root SRCDIR to the cbmc
            root CBMCDIR (see --srcdir SRCDIR), typically 'test/cbmc'.
            CBMCDIR contains all code written
            specifically to build the proofs and typically also includes
            the proofs themselves.  All code under CBMCDIR
            is considered to be a proof stub.  By default, if CBMCPATH
            is not specified, then CBMCDIR is the parent of PROOFDIR
            (see --proofdir PROOFDIR), and CBMCPATH is the relative
            path from SRCDIR to CBMCDIR (see --srcdir SRCDIR). """
        },
        {
            "flag": "--jsonpath",
            "help": """
            The relative path from the proof directory to the json
            directory containing cbmc-viewer output, typically
            'report/json' where 'report' is the string specified by
            the --reportdir or --htmldir flag to cbmc-viewer.  By
            default, if JSONPATH is not specified, use the path from a
            proof directory to a directory containing the file
            'viewer-result.json'. """
        },
        {
            "flag": "--stubbed-usage",
            "action": "store_true",
            "help": """
            Summarize stubbed function usage by "name" mapping each
            function to the proofs using the stub and by "count"
            giving a histogram mapping each function to the number of
            times it is used. """
        },
        {
            "flag": "--removed-usage",
            "action": "store_true",
            "help": """
            Summarize removed function usage by "name" mapping each
            function to the proofs using the stub and by "count"
            giving a histogram mapping each function to the number of
            times it is used. """
        },
        {
            "flag": "--missing-usage",
            "action": "store_true",
            "help": """
            Summarize missing function usage by "name" mapping each
            function to the proofs using the stub and by "count"
            giving a histogram mapping each function to the number of
            times it is used. """
        },
        {
            "flag": "--config",
            "default": "cbmc-viewer.json",
            "help": """
            Name of the cbmc-viewer configuration file.
            (Default: %(default)s)
            """
        },
        {
            "flag": "--viewer-reachable",
            "default": "viewer-reachable.json",
            "help": """
            Name of the cbmc-viewer summary of reachable functions.
            (Default: %(default)s) """
        },
        {
            "flag": "--viewer-result",
            "default": "viewer-result.json",
            "help": """
            Name of the cbmc-viewer summary of results.
            (Default: %(default)s) """
        },
        {
            "flag": "--verbose",
            "action": "store_true",
            "help": "Verbose output"
        },
        {
            "flag": "--debug",
            "action": "store_true",
            "help": "Debug output"
        }
    ]
    epilog = """
    The simplest way to use the script is to run '%(prog)s' in the directory
    that is the root of the proof tree (usually called 'proofs').
    """

    parser = argparse.ArgumentParser(description=desc, epilog=epilog)
    for arg in args:
        flag = arg['flag']
        del arg['flag']
        parser.add_argument(flag, **arg)
    return parser

def parse_arguments(args=None):
    return create_parser().parse_args(args=args)

def configure_logger(verbose=False, debug=False):
    # Logging is configured by the first invocation of logging.basicConfig
    fmt = '%(levelname)s: %(message)s'
    if debug:
        logging.basicConfig(level=logging.DEBUG, format=fmt)
    if verbose:
        logging.basicConfig(level=logging.INFO, format=fmt)
    logging.basicConfig(format=fmt)

################################################################
# Shell out commands

def run(cmd, cwd=None, encoding=None):
    """Run a command in a subshell and return the standard output.

    Run the command cmd in the directory cwd and use encoding to
    decode the standard output.
    """

    kwds = {
        'cwd': cwd,
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE,
        'text': True,
    }
    if sys.version_info >= (3, 6): # encoding introduced in Python 3.6
        kwds['encoding'] = encoding

    logging.debug('Running "%s" in %s', ' '.join(cmd), cwd)

    result = subprocess.run(cmd, **kwds, check=False)
    if result.returncode:
        logging.debug('Failed command: %s', ' '.join(cmd))
        logging.debug('Failed return code: %s', result.returncode)
        logging.debug('Failed stdout: %s', result.stdout.strip())
        logging.debug('Failed stderr: %s', result.stderr.strip())
        return []

    # Remove line continuations before splitting stdout into lines
    # Running command with text=True converts line endings to \n in stdout
    lines = result.stdout.replace('\\\n', ' ').splitlines()
    return [strip_whitespace(line) for line in lines]

def strip_whitespace(string):
    return re.sub(r'\s+', ' ', string).strip()

################################################################
# Load viewer JSON data

def load_json(name="", path=None):
    res = {}
    try:
        with open(path, encoding="utf-8") as handle:
            res = json.load(handle)
    except TypeError:
        logging.debug("%s file name %s is not a string", name, path)
    except FileNotFoundError:
        logging.debug("Can't open %s file %s", name, path)
    except json.decoder.JSONDecodeError:
        logging.debug("Can't parse %s file %s as json", name, path)
    return res

def load_config(path=None):
    path = path or 'cbmc-viewer.json'
    return load_json("config", path)

def load_viewer_result(path=None):
    path = path or 'report/json/viewer-result.json'
    return load_json("viewer result", path)

def load_viewer_reachable(path=None):
    path = path or 'report/json/viewer-reachable.json'
    return load_json("viewer reachable", path)

################################################################
# Parse viewer JSON data

def load_reachable_functions(path=None):
    reachable = load_viewer_reachable(path)
    return reachable.get('viewer-reachable', {}).get('reachable', [])

def load_missing_functions(path=None):

    def missing(warning):
        if warning.strip().startswith('**** WARNING: no body for function'):
            return warning.strip().split()[-1]
        return None

    result = load_viewer_result(path)
    warnings = result.get('viewer-result', {}).get('warning', [])
    return [fcn for fcn in [missing(warning) for warning in warnings] if fcn]

def load_expected_missing_functions(path=None):
    config = load_config(path)
    return config.get('expected-missing-functions', [])

################################################################
# Summarize proof abstraction

def is_builtin(path):
    if not path:
        logging.info("Can't test for builtin: path %s is empty", path)
        return False

    path = os.path.normpath(path)
    name = os.path.split(path)[-1]
    return name.startswith('<built-in') or name.startswith('<builtin-')

def is_cbmc_file(path, cbmcpath):
    if not path or not cbmcpath:
        logging.info("Can't test for cbmc stub: "
                     "path %s or cbmcpath %s is empty", path, cbmcpath)
        return True # Assume everything is a stub

    path = os.path.normpath(path)
    cbmcpath = os.path.normpath(cbmcpath)
    return cbmcpath == os.path.commonpath([path, cbmcpath])

def is_cbmc_harness(path, harness_suffix="harness"):
    if not path:
        logging.info("Can't test for cbmc harness: path %s is empty", path)
        return False

    path = os.path.normpath(path)
    basename = os.path.basename(path)
    name = os.path.splitext(basename)[0]
    return name.endswith(harness_suffix)

def stubbed_reachable_functions(reachable, cbmcpath):
    reachable = {
        path: functions for path, functions in reachable.items()
        if is_cbmc_file(path, cbmcpath)
        and not is_builtin(path)
        and not is_cbmc_harness(path)
    }
    return { path: sorted(set(reachable[path]))
             for path in sorted(reachable) if reachable[path]}

def expected_missing_functions(missing, expected):
    return sorted([fcn for fcn in missing if fcn in expected])

def unexpected_missing_functions(missing, expected):
    return sorted([fcn for fcn in missing if fcn not in expected])

################################################################

def scan_proof(proof, args):
    reachable = load_reachable_functions(
        os.path.join(args.proofdir, proof, args.jsonpath, args.viewer_reachable)
    )
    missing = load_missing_functions(
        os.path.join(args.proofdir, proof, args.jsonpath, args.viewer_result)
    )
    expected = load_expected_missing_functions(
        os.path.join(args.proofdir, proof, args.config)
    )

    return {
        'stubbed': stubbed_reachable_functions(reachable, args.cbmcpath),
        'removed': expected_missing_functions(missing, expected),
        'missing': unexpected_missing_functions(missing, expected),
    }

def scan_proofs(proofs, args):

    # Don't bother to map proofs to scans in the special case that the
    # only proof directory is the current directory.
    if proofs == ['.']:
        return scan_proof('.', args)

    return { proof: scan_proof(proof, args) for proof in sorted(proofs)}

################################################################
# Extract a cbmc-viewer command from make or litani

def command_name(command):
    """Extract command name from command line.

    Assume that the first word in the command is the path to the
    binary (and not, for example, an environment variable definition).
    """

    return os.path.basename(command.strip().split()[0])

def is_viewer_command(command, viewer_names=None):
    """Is the command an invocation of cbmc-viewer?

    Assume that the first word in the command is the path to the
    binary (and not, for example, an environment variable definition).
    Assume that the valid names for the cbmc-viewer (the file name)
    are in viewer_names.
    """

    viewer_names = viewer_names or ['cbmc-viewer']

    if not command: # eg, blank line
        return False
    return command_name(command) in viewer_names

def is_litani_command(command, litani_names=None):
    """Is the command an invocation of litani?

    Assume that the first word in the command is the path to the
    binary (and not, for example, an environment variable definition).
    Assume that the valid names for the litani binary (the file name)
    are in litani_names.
    """

    litani_names = litani_names or ['litani']

    if not command: # eg, blank line
        return False
    return command_name(command) in litani_names

def extract_command_from_litani_command(command):
    """Extract the shell command from a litani command."""

    command = command.strip()
    match1 = re.search(' --command +"([^"]*)"', command)
    match2 = re.search(" --command +'([^']*)'", command)
    match3 = re.search(' --command +([^ ]*)', command)
    cmd1 = match1.group(1).strip() if match1 else None
    cmd2 = match2.group(1).strip() if match2 else None
    cmd3 = match3.group(1).strip() if match3 else None

    cmd = cmd1 or cmd2 or cmd3
    return cmd if cmd else command

def get_make_commands(proof=None):
    """Get the list of commands invoked by make to run the proof."""

    return run(['make', '-nB'], cwd=proof)

def extract_viewer_command(commands):
    """Extract the invocation of cbmc-viewer from the commands invoked by make.
    """

    commands = [extract_command_from_litani_command(cmd) for cmd in commands]
    viewer_commands = [cmd for cmd in commands if is_viewer_command(cmd)]
    if len(viewer_commands) != 1:
        logging.debug("Unexpected list of cbmc-viewer commands: %s",
                      viewer_commands)
        return None

    return viewer_commands[0]

def get_viewer_command_from_make(proof=None):

    # This function will fail with the starter kit.
    #
    # The stater kit runs cbmc-viewer by pushing a variable VIEWER_CMD
    # to the environment and running litani with '--command $VIEWER_CMD'.
    # The make output includes this command with the variable unexpanded.

    command = extract_viewer_command(get_make_commands(proof))
    if not command:
        logging.info("Can't find cbmc-viewer command in make output.")
        return None

    return command

def get_viewer_command_from_litani(proofdir):

    # Litani output is written to a directory named 'output' in the
    # current working directory.  This output includes a file with
    # a name like
    #   output/litani/runs/36c0b562-7535-4ff5-94be-bae5459ba6d2/run.json
    # that includes all commands run by litani, including the fully
    # expanded invocation of cbmc-viewer.

    try:
        runs = run(['find', 'output', '-name', 'run.json'], cwd=proofdir)
        if not runs:
            logging.info("Can't find cbmc-viewer command in litani output.")
            return None
    except: # pylint: disable=bare-except
        logging.info("Can't find cbmc-viewer command in litani output: "
                     "can't find litani output.")
        return None

    with open(os.path.join(proofdir, runs[0]), encoding="utf-8") as handle:
        log = json.load(handle)

    cmd = log['pipelines'][0]['ci_stages'][-1]['jobs'][0]['wrapper_arguments']['command'] # pylint: disable=line-too-long
    cmd = strip_whitespace(cmd)
    assert cmd.startswith('cbmc-viewer')
    return cmd

def get_viewer_command(proofdir, proof):

    return (
        get_viewer_command_from_make(os.path.join(proofdir, proof)) or
        get_viewer_command_from_litani(proofdir)
    )

################################################################
# Extract flags from a cbmc-viewer command

def extract_viewer_flag(flag, command):
    try:
        words = command.strip().split()
        index = words.index(flag)
        return os.path.normpath(words[index+1])
    except ValueError:
        logging.debug("Can't find flag %s in command %s", flag, command)
    except IndexError:
        logging.debug("Can't find flag %s argument in command %s",
                      flag, command)
    return None

def extract_srcdir(command):
    return extract_viewer_flag('--srcdir', command)

def extract_reportdir(command):
    return (
        extract_viewer_flag('--reportdir', command) # Viewer 2.0
        or
        extract_viewer_flag('--htmldir', command)   # Viewer 1.0 legacy
    )

################################################################
# Find paths to viewer-results.json summaries produced by cbmc-viewer

def viewer_result_paths(args):

    # Find all copies of viewer-result.json under the proof directory
    cmd = ['find', '.', '-name', args.viewer_result]
    viewer_results = run(cmd, cwd=args.proofdir)

    # Clean up find output
    viewer_results = [os.path.normpath(result) for result in viewer_results]

    # Ignore litani copies of viewer-result.json
    viewer_results = [result for result in viewer_results
                      if not result.startswith('output/latest')
                      and not result.startswith('output/litani/runs')]

    return viewer_results

################################################################
# Guess missing flags from paths to viewer-result.json

def guess_proof_from_result_paths(args, result_paths):

    if args.proof: # don't guess, already defined
        return args.proof

    # CBMC viewer puts viewer-result.json under report/json in every
    # proof directory where report is the value of the --reportdir
    # flag to viewer.
    #
    # Assume the directory three levels above viewer-result.json is a
    # proof directory.

    proofs = [
        os.path.normpath(
            os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.normpath(result_path)))))
        for result_path in result_paths]
    proofs = sorted(set(proofs))

    assert len(proofs) > 0
    return proofs

def guess_jsonpath_from_result_paths(args, result_paths):

    if args.jsonpath: # don't guess, already defined
        return args.jsonpath

    # CBMC viewer puts viewer-result.json under report/json in every
    # proof directory where report is the value of the --reportdir
    # flag to viewer.
    #
    # Assume the directory two levels above viewer-result.json is reportdir.

    reportdirs = [
        os.path.normpath(
            os.path.basename(os.path.dirname(os.path.dirname(
                os.path.normpath(result_path)))))
        for result_path in result_paths]
    reportdirs = sorted(set(reportdirs))

    assert len(reportdirs) == 1
    reportdir = reportdirs[0]

    return os.path.normpath(os.path.join(reportdir, 'json'))

################################################################
# Guess missing flags from flags to cbmc-viewer command

def guess_jsonpath_from_viewer_command(args, viewer_command):

    if args.jsonpath: # don't guess, already defined
        return args.jsonpath

    reportdir = extract_reportdir(viewer_command)
    if not reportdir:
        return args.jsonpath

    return os.path.normpath(os.path.join(reportdir, 'json'))

def guess_srcdir_from_viewer_command(args, viewer_command):

    if args.srcdir: # don't guess, already defined
        return args.srcdir

    assert len(args.proof) > 0 # validated by guess_proof()
    proof = [args.proofdir, args.proof[0]]

    viewer_command = get_viewer_command(*proof)
    if not viewer_command:
        logging.info("Can't guess srcdir: cbmc-viewer command not found.")
        return args.cbmcpath

    srcdir = extract_srcdir(viewer_command)
    if not srcdir:
        logging.info("Can't guess srcdir: "
                     "--srcdir not found in cbmc-viewer command: %s",
                     viewer_command)
        return args.cbmcpath

    return os.path.abspath(srcdir)

################################################################
# Guess flags from other arguments

def guess_cbmcpath_from_args(args):

    if args.cbmcpath: # don't guess, already defined
        return args.cbmcpath

    # Guess cbmcpath from srcdir and proofdir
    if not args.srcdir:
        logging.info("Can't guess cbmcpath: srcdir is empty.")
        return args.cbmcpath
    if not args.proofdir:
        logging.info("Can't guess cbmcpath: proofdir is empty.")
        return args.cbmcpath

    # Guess that cbmcdir is the parent of proofdir, and guess that
    # cbmcpath is the path from srcdir to cbmcdir.
    proofdir = os.path.abspath(args.proofdir)
    srcdir = os.path.abspath(args.srcdir)
    cbmcpath = os.path.relpath(os.path.dirname(proofdir), srcdir)

    if cbmcpath.startswith('..'):
        logging.info("Can't guess cbmcpath: "
                     "srcdir %s does not contain proofdir %s",
                     srcdir, proofdir)
        return args.cbmcpath

    return cbmcpath

################################################################
# Compute  histogram

def defined_histogram(summary, key='stubbed'):
    histogram_by_name = {}
    for proof, proof_summary in summary.items():
        for _, stubbed_functions in proof_summary[key].items():
            for stub in stubbed_functions:
                histogram_by_name[stub] = histogram_by_name.get(stub, [])
                histogram_by_name[stub].append(proof)

    counts = [(stub, len(users)) for stub, users in histogram_by_name.items()]
    counts = sorted(counts, key=lambda pair: (pair[1], pair[0]), reverse=True)
    histogram_by_count = {pair[0]: pair[1] for pair in counts}

    return {"name": histogram_by_name, "count": histogram_by_count}

def undefined_histogram(summary, key):
    histogram_by_name = {}
    for proof, proof_summary in summary.items():
        for undefined in proof_summary[key]:
            histogram_by_name[undefined] = histogram_by_name.get(undefined, [])
            histogram_by_name[undefined].append(proof)

    counts = [(func, len(users)) for func, users in histogram_by_name.items()]
    counts = sorted(counts, key=lambda pair: (pair[1], pair[0]), reverse=True)
    histogram_by_count = {pair[0]: pair[1] for pair in counts}

    return {"name": histogram_by_name, "count": histogram_by_count}


################################################################

def compute_default_arguments(args):

    # Ensure absolute paths to important directories
    if args.proofdir:
        args.proofdir = os.path.abspath(args.proofdir)
    if args.srcdir:
        args.srcdir = os.path.abspath(args.srcdir)
    if args.proof:
        args.proof = [os.path.normpath(proof) for proof in args.proof]

    assert args.proofdir
    result_paths = viewer_result_paths(args)
    args.proof = guess_proof_from_result_paths(args, result_paths)
    args.jsonpath = guess_jsonpath_from_result_paths(args, result_paths)

    assert args.proofdir
    assert args.proof
    viewer_command = get_viewer_command(args.proofdir, args.proof[0])
    args.jsonpath = guess_jsonpath_from_viewer_command(args, viewer_command)
    args.srcdir = guess_srcdir_from_viewer_command(args, viewer_command)

    args.cbmcpath = guess_cbmcpath_from_args(args)

    return args

def log_arguments(args, text=''):
    label = ' '.join(['ARG', text]).strip()
    for arg in dir(args):
        if not arg.startswith('_'):
            logging.info('%s: %s: %s', label, arg, getattr(args, arg))


def main():
    args = parse_arguments()
    configure_logger(args.verbose, args.debug)
    log_arguments(args)

    args = compute_default_arguments(args)
    log_arguments(args)

    summary = scan_proofs(args.proof, args)
    if args.stubbed_usage:
        print(json.dumps(defined_histogram(summary, 'stubbed'), indent=2))
        return
    if args.removed_usage:
        print(json.dumps(undefined_histogram(summary, 'removed'), indent=2))
        return
    if args.missing_usage:
        print(json.dumps(undefined_histogram(summary, 'missing'), indent=2))
        return
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
