#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Differential testing of cbmc-viewer."""

from pathlib import Path
import copy
import json
import logging
import os
import re
import shutil
import subprocess
import sys

import arguments


################################################################
# Parse command line arguments and configure logging

def parse_arguments():
    """Parse command line arguemnts"""

    description = """
       Differential testing of cbmc-viewer.  Run two versions of
       cbmc-viewer on the output of cbmc and collect the results in
       two directories for easy comparison.  The script assumes the
       proofs are run using litani (for example, by running the
       script run-cbmc-proofs.py in the cbmc starter kit).
       """
    options = [
        {'flag': '--proofs',
         'type': Path,
         'help':
         """
         The directory containing the proofs.  This is the directory
         in which litani was run (the directory cbmc/proofs containing the script
         run-cbmc-proofs.py in the cbmc starter kit)
         and the directory in which litani wrote the file .litani-cache-dir.
         """
        },
        {'flag': '--viewer-repository',
         'type': Path,
         'default': '.',
         'help': "The root of the cbmc-viewer repository.  Defaults to '%(default)s'."
        },
        {'flag': '--commits',
         'type': str,
         'default': [],
         'nargs': '*',
         'help':
         """
         The two versions of cbmc-viewer to compare.  The versions are
         specified by giving names of commits or branches in the
         cbmc-viewer repository.
         """
        },
        {'flag': '--reports',
         'type': Path,
         'default': [],
         'nargs': '*',
         'help':
         """
         The two report directories into which the two sets of reports generated by the
         cbmc-viewer will be written.  The report for any given proof will be stored
         in a subdirectory having the name of the proof.  Defaults to
         '/tmp/reports/commit1' and '/tmp/reports/commit2'.
         """
        },
        {'flag': '--installs',
         'type': Path,
         'default': [],
         'nargs': '*',
         'help':
         """
         The two installation directories into which the two versions of cbmc-viewer
         will be installed (as python virtual environments).  Defaults to
         '/tmp/viewer/commit1' and '/tmp/viewer/commit2'.
         """
        },
        {'flag': '--litani',
         'type': Path,
         'default': 'litani',
         'help': "Command to invoke litani.  Defaults to '%(default)s'."},
        {'flag': '--force',
         'action': 'store_true',
         'help': 'Overwrite existing report or installation directories'},
    ]
    args = arguments.create_parser(options, description).parse_args()
    arguments.configure_logging(args)
    return args

################################################################
# Run a command

def run(cmd, stdin=None, check=True, env=None, cwd=None, capture_output=True):
    """Run a command as a subprocess"""

    cmd = [str(word) for word in cmd]
    stdin = str(stdin) if stdin is not None else None
    kwds = {
        "env": env,
        "cwd": cwd,
        "text": True,
        "stdout": subprocess.PIPE if capture_output else None,
        "stderr": subprocess.PIPE if capture_output else None,
    }
    with subprocess.Popen(cmd, **kwds) as pipe:
        stdout, stderr = pipe.communicate(input=stdin)
    if check and pipe.returncode:
        logging.debug("Command %s returned %s", cmd, pipe.returncode)
        for line in stderr.splitlines():
            logging.debug(line)
        raise UserWarning(f"Command '{' '.join(cmd)}' returned '{pipe.returncode}'")
    if not capture_output:
        return None
    return [line.rstrip() for line in stdout.splitlines()]

################################################################

def install_viewer(viewer_commit, venv_root, viewer_repo):
    """Install a given version of viewer into a virtual environment"""

    # save the original commit
    branch = run(["git", "branch", "--show-current"], cwd=viewer_repo)[0]
    run(["git", "stash"], cwd=viewer_repo)

    try:
        logging.info("Setting up virtual environment %s for viewer %s", venv_root, viewer_commit)
        run(["python3", "-m", "venv", venv_root])
        venv_bin = Path(venv_root) / "bin"
        env = dict(os.environ.items())
        env['PATH'] = str(venv_bin) + os.pathsep + env['PATH']
        run(["python3", "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel", "build"],
            env=env)

        logging.info("Installing viewer %s into virtual environment %s", viewer_commit, venv_root)
        run(["git", "checkout", viewer_commit], cwd=viewer_repo, env=env)
        run(["make", "install"], cwd=viewer_repo, env=env)

        venv_viewer = venv_bin / "cbmc-viewer"
        return venv_viewer
    except UserWarning as error:
        logging.info("Failed to install viewer %s into virtual environment %s",
                     viewer_commit, venv_root)
        logging.info(error)
        raise

    finally:
        logging.info("Restoring viewer repository to %s", branch)
        run(["git", "checkout", branch], cwd=viewer_repo)
        try:
            run(["git", "stash", "pop"], cwd=viewer_repo)
        except UserWarning:
            # Probably means prior 'git stash' found nothing to stash
            # Consider checking `git status --porcelain` to cover this case
            pass

################################################################
# Reconstruct the litani add-job commands used to run viewer

def load_run_json(proof_root):
    """Load run.json generated by running run-cbmc-proofs.py in proof_root"""

    run_json = run(['litani', 'dump-run'], cwd=proof_root)
    return json.loads(' '.join(run_json))

def viewer_wrappers(run_json):
    """Litani wrappers for viewer jobs in run.json"""

    for pipeline in run_json["pipelines"]:
        for ci_stage in pipeline["ci_stages"]:
            for job in ci_stage["jobs"]:
                wrapper = job["wrapper_arguments"]
                if wrapper["ci_stage"] == "report":
                    yield wrapper

def add_job_command(wrapper):
    """Reconstruct a litani add-job command from its wrapper in run.json"""

    return {
        "--command": wrapper["command"],
        "--inputs": wrapper["inputs"],
        "--outputs": wrapper["outputs"],
        "--pipeline-name": wrapper["pipeline_name"],
        "--stdout-file": wrapper["stdout_file"],
        "--interleave-stdout-stderr": wrapper["interleave_stdout_stderr"],
        "--ci-stage": wrapper["ci_stage"],
        "--description": wrapper["description"]
    }

def viewer_add_job_commands(proof_root):
    """The litani add-job commands used to invoke viewer"""

    run_json = load_run_json(proof_root)
    wrappers = viewer_wrappers(run_json)
    return [add_job_command(wrapper) for wrapper in wrappers]

################################################################
# Update a viewer job to use a different viewer and a different report directory

def viewer_options_without_reportdir(viewer_command):
    """Strip --reportdir from command line options used to invoke viewer."""

    command = re.sub(r'\s+', ' ', viewer_command.strip())

    # strip path used to invoke viewer from front of command
    options = command.split(' ', 1)[-1]
    # strip --reportdir option from within command
    options = re.sub(r'--reportdir\s+[^\s]+', '', options)

    return re.sub(r'\s+', ' ', options.strip())

def form_reportdir(report_root, proof_name):
    reportdir = Path(report_root) / Path(proof_name)
    return str(reportdir)

def update_command(command, new_viewer, new_reportdir):
    options = viewer_options_without_reportdir(command)
    return ' '.join([str(new_viewer), options, '--reportdir', new_reportdir])

def update_job(job, new_viewer, new_report_root):

    job = copy.copy(job) # a shallow copy of job
    command = job["--command"]
    outputs = job["--outputs"]
    proof_name = job["--pipeline-name"]
    assert len(outputs) == 1

    new_reportdir = form_reportdir(new_report_root, proof_name)
    job["--command"] = update_command(command, new_viewer, new_reportdir)
    job["--outputs"] = [new_reportdir]
    return job

def update_jobs(jobs, new_viewer, new_report_root):
    return [update_job(job, new_viewer, new_report_root) for job in jobs]

################################################################

def run_viewer(proof_root, viewer1, root1, viewer2, root2, litani):
    logging.info("Loading and updating viewer jobs...")
    viewer_jobs = viewer_add_job_commands(proof_root)
    jobs = update_jobs(viewer_jobs, viewer1, root1) + update_jobs(viewer_jobs, viewer2, root2)

    logging.info("Running litani init...")
    run([litani, "init", "--project", "Differential testing"])

    for job in jobs:
        cmd = [litani, "add-job"]
        for flag, value in job.items():
            cmd.append(flag)
            if isinstance(value, bool):
                continue
            if isinstance(value, list):
                cmd.extend(value)
            else:
                cmd.append(value)
        logging.info("Running litani add-job...")
        run(cmd)

    logging.info("Running litani run-build...")
    run([litani, "run-build"], capture_output=False)

################################################################

def compare_reports(reports1, reports2):
    logging.info("Comparing %s and %s...", reports1, reports2)
    try:
        run(["diff", "-r", reports1, reports2])
    except UserWarning as error:
        raise UserWarning(
            f"Reports differ: compare with 'diff -r {reports1} {reports2}'") from error

################################################################
# Validate command line arguments

def check_git_status(repo):
    try:
        status = run(["git", "status", "--porcelain"], cwd=repo)
    except UserWarning as error:
        raise UserWarning("This is not a git repository: git status failed") from error
    if status:
        raise UserWarning("This git repository has uncomitted changes.")
    return True

def validate_litani(litani):
    logging.debug("--litani = %s", litani)
    path = shutil.which(litani)
    if path:
        return path
    raise UserWarning("Use --litani to give the command to invoke litani")

def validate_repository(repo):
    logging.debug("--viewer-repository = %s", repo)
    if (repo / '.git').is_dir():
        return repo
    raise UserWarning("Use --viewer-repository to give the root of the cbmc-viewer repository")

def validate_proofs(proofs):
    logging.debug("--proofs = %s", proofs)
    if (proofs / '.litani_cache_dir').is_file():
        return proofs
    raise UserWarning("Use --proofs to specify a proofs directory (containing .litani_cache_dir)")

def validate_commits(commits):
    logging.debug("--commits = %s", commits)
    commits = commits or []
    try:
        cmd = ['git', 'rev-parse', '--verify', '--quiet', '--end-of-options']
        run([*cmd, commits[0]])
        run([*cmd, commits[1]])
        return commits
    except (UserWarning, IndexError) as error:
        raise UserWarning("Use --commits to specify two commits or branches to compare") from error

def validate_reports(reports, commits, force):
    logging.debug("--reports = %s", reports)
    reports = reports or []
    commits = commits or []

    try:
        if len(reports) not in [0, 2]:
            raise IndexError

        if len(reports) == 0:
            tmp = Path('/tmp/reports')
            reports = [tmp/commits[0], tmp/commits[1]]

        if reports[0] == reports[1]:
            name = reports[0].name # reports[0].name == reports[1].name
            for idx in [0, 1]:
                reports[idx] = reports[idx].with_name(name + str(idx))

        for report in reports:
            if report.exists() and not force:
                raise UserWarning(f"Path {report} exists: use --force to overwrite")

        return reports
    except IndexError as error:
        raise UserWarning("Use --reports to specify two report directories.") from error

def validate_installs(installs, commits, force):
    logging.debug("--installs = %s", installs)
    installs = installs or []
    commits = commits or []

    try:
        if len(installs) not in [0, 2]:
            raise IndexError

        if len(installs) == 0:
            tmp = Path('/tmp/viewer')
            installs = [tmp/commits[0], tmp/commits[1]]

        if installs[0] == installs[1]:
            name = installs[0].name # installs[0].name == installs[1].name
            for idx in [0, 1]:
                installs[idx] = installs[idx].with_name(name + str(idx))

        for install in installs:
            if install.exists() and not force:
                raise UserWarning(f"Path {install} exists: use --force to overwrite")

        return installs
    except IndexError as error:
        raise UserWarning("Use --installs to specify two install directories.") from error

def validate_arguments(args):
    try:
        args.viewer_repository = validate_repository(args.viewer_repository)
        check_git_status(args.viewer_repository)
        args.litani = validate_litani(args.litani)
        args.proofs = validate_proofs(args.proofs)
        args.commits = validate_commits(args.commits)
        args.reports = validate_reports(args.reports, args.commits, args.force)
        args.installs = validate_installs(args.installs, args.commits, args.force)
    except UserWarning as error:
        logging.error(error)
        sys.exit(1)

################################################################

def main():
    args = parse_arguments()
    validate_arguments(args)

    shutil.rmtree(args.reports[0], ignore_errors=True)
    shutil.rmtree(args.reports[1], ignore_errors=True)
    shutil.rmtree(args.installs[0], ignore_errors=True)
    shutil.rmtree(args.installs[1], ignore_errors=True)

    viewer1 = install_viewer(args.commits[0], args.installs[0], args.viewer_repository)
    report1 = args.reports[0]
    viewer2 = install_viewer(args.commits[1], args.installs[1], args.viewer_repository)
    report2 = args.reports[1]

    run_viewer(args.proofs, viewer1, report1, viewer2, report2, args.litani)
    compare_reports(report1, report2)

if __name__ == "__main__":
    main()

################################################################
