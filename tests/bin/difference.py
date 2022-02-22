#!/usr/bin/env python3

import argparse
import copy
import json
import logging
import os
import re
import shutil
import subprocess
import sys

from pathlib import Path

################################################################
# Parse command line arguments and configure logging

def parse_arguments():
    """Parse command line arguemnts"""

    parser = argparse.ArgumentParser(description=
       """
       Differential testing of cbmc-viewer.  Run two versions of
       cbmc-viewer on the output of cbmc and collect the results in
       two directories for easy comparison.  The script assumes the
       proofs are run using litani (for example, by running the
       script run-cbmc-proofs.py in the cbmc starter kit).
       """
    )
    options = [
        {'flag': '--proofs',
         'help':
         """
         The directory containing the proofs.  This is the directory
         in which litani was run (the directory cbmc/proofs containing the script
         run-cbmc-proofs.py in the cbmc starter kit)
         and the directory in which litani wrote the file .litani-cache-dir.
         """
        },
        {'flag': '--viewer-repository',
         'default': '.',
         'help': "The root of the cbmc-viewer repository.  Defaults to '%(default)s'."
        },
        {'flag': '--commits',
         'nargs': '*',
         'help':
         """
         The two versions of cbmc-viewer to compare.  The versions are
         specified by giving names of commits or branches in the
         cbmc-viewer repository.
         """
        },
        {'flag': '--reports',
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
         'nargs': '*',
         'help':
         """
         The two installation directories into which the two versions of cbmc-viewer
         will be installed (as python virtual environments).  Defaults to
         '/tmp/viewer/commit1' and '/tmp/viewer/commit2'.
         """
        },
        {'flag': '--litani',
         'default': 'litani',
         'help': "Command to invoke litani.  Defaults to '%(default)s'."},
        {'flag': '--force',
         'action': 'store_true',
         'help': 'Overwrite existing report or installation directories'},
        {'flag': '--verbose',
         'action': 'store_true',
         'help': 'Verbose output'},
        {'flag': '--debug',
         'action': 'store_true',
         'help': 'Debug output'},
    ]
    for option in options:
        flag = option.pop('flag')
        parser.add_argument(flag, **option)
    return parser.parse_args()

def configure_logging(verbose=False, debug=False):
    """Configure logging"""

    if debug:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
        return
    if verbose:
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        return
    logging.basicConfig(format='%(levelname)s: %(message)s')

################################################################
# Run a command

def run(cmd, check=True, capture_output=True, env=None, cwd=None):
    """Run a command as a subprocess"""

    kwds = {
        "capture_output": capture_output,
        "env": env,
        "cwd": cwd,
        "text": True
    }
    logging.debug("Running command: %s", ' '.join(cmd))
    proc = subprocess.run(cmd, **kwds, check=check)
    if capture_output:
        stdout = proc.stdout.strip().splitlines()
        stderr = proc.stderr.strip().splitlines()
        for line in stdout + stderr:
            logging.debug(line)
        return stdout
    return None

################################################################

def install_viewer(viewer_commit, venv_root, viewer_repo):
    """Install a given version of viewer into a virtual environment"""

    # save the original commit
    branch = run(["git", "branch", "--show-current"], cwd=viewer_repo, capture_output=True)[0]
    run(["git", "stash"], cwd=viewer_repo)

    try:
        logging.info("Setting up virtual environment %s for viewer %s", venv_root, viewer_commit)
        run(["python3", "-m", "venv", venv_root])
        venv_bin = Path(venv_root) / Path("bin")
        env = dict(os.environ.items())
        env['PATH'] = str(venv_bin) + os.pathsep + env['PATH']
        run(["python3", "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel", "build"],
            env=env)

        logging.info("Installing viewer %s into virtual environment %s", viewer_commit, venv_root)
        run(["git", "checkout", viewer_commit], cwd=viewer_repo, env=env)
        run(["make", "install"], cwd=viewer_repo, env=env)

        venv_viewer = venv_bin / Path("cbmc-viewer")
        return str(venv_viewer)

    except subprocess.CalledProcessError as error:
        logging.info("Failed to install viewer %s into virtual environment %s",
                     viewer_commit, venv_root)
        logging.info(str(error))
        raise error

    finally:
        logging.info("Restoring viewer repository to %s", branch)
        run(["git", "checkout", branch], cwd=viewer_repo)
        try:
            run(["git", "stash", "pop"], cwd=viewer_repo)
        except subprocess.CalledProcessError as err:
            # Status 1 probably means prior 'git stash' found nothing to stash
            if err.returncode != 1:
                raise err

################################################################
# Reconstruct the litani add-job commands used to run viewer

def load_run_json(proof_root):
    """Load run.json generated by running run-cbmc-proofs.py in proof_root"""

    logging.debug("CBMC proof root: %s", proof_root)
    with open(Path(proof_root) / Path(".litani_cache_dir"), encoding="utf8") as litani_cache_dir:
        cache = litani_cache_dir.read().strip()

    logging.debug("Litani cache directory: %s", cache)
    with open(Path(cache) / Path("run.json"), encoding="utf8") as run_json:
        return json.load(run_json)

def extract_viewer_jobs(run_json):
    """Extract the viewer jobs from run.json"""

    jobs = []
    for pipeline in run_json["pipelines"]:
        for ci_stage in pipeline["ci_stages"]:
            for job in ci_stage["jobs"]:
                wrapper = job["wrapper_arguments"]
                if wrapper["ci_stage"] == "report":
                    jobs.append(wrapper)

    return jobs

def reconstruct_add_job_command(wrapper):
    """Reconstruct the litani add-job command from its wrapper description in run.json"""

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
    viewer_jobs = extract_viewer_jobs(run_json)
    return [reconstruct_add_job_command(job) for job in viewer_jobs]

################################################################
# Update a viewer job to use a different viewer and a different report directory

def viewer_options_without_reportdir(viewer_command):
    """The arguments used to invoke viewer, but omitting --reportdir"""

    # Warning: using whitespace to parse a command line is brittle
    words = re.split(r'\s+', viewer_command.strip())
    words.pop(0) # first word is the viewer script itself

    # Warning: using position to parse command line arguments is brittle
    options = []
    reportdir_option = False
    for word in words:
        if word == '--reportdir': # word is reportdir option
            reportdir_option = True
            continue
        if reportdir_option: # word is reportdir option argument
            reportdir_option = False
            continue
        options.append(word)

    return options

def form_reportdir(report_root, proof_name):
    reportdir = Path(report_root) / Path(proof_name)
    return str(reportdir)

def update_command(command, new_viewer, new_reportdir):
    options = viewer_options_without_reportdir(command)
    return ' '.join([new_viewer, *options, '--reportdir', new_reportdir])

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
    except subprocess.CalledProcessError as error:
        raise UserWarning("Reports differ: compare with 'diff -r {reports1} {reports2}'") from error

################################################################
# Validate command line arguments

def check_git_status(repo):
    try:
        status = run(["git", "status", "--porcelain"], cwd=repo, capture_output=True)
    except subprocess.CalledProcessError as error:
        raise UserWarning("This is not a git repository: git status failed") from error
    if status:
        raise UserWarning("This git repository has uncomitted changes.")
    return True

def validate_litani(litani):
    logging.debug("--litani = %s", litani)
    try:
        return run(["which", litani], capture_output=True)[0]
    except subprocess.CalledProcessError as error:
        raise UserWarning("Use --litani to give the command invoking litani") from error

def validate_repository(repo):
    logging.debug("--viewer-repository = %s", repo)
    try:
        assert isinstance(repo, str)
        assert os.path.exists(f"{repo}{os.sep}.git")
        return repo
    except AssertionError as error:
        raise UserWarning(
            "Use --viewer-repository to give the root of the cbmc-viewer repository"
        ) from error

def validate_proofs(proofs):
    logging.debug("--proofs = %s", proofs)
    try:
        assert isinstance(proofs, str)
        assert os.path.exists(f"{proofs}{os.sep}.litani_cache_dir")
        return proofs
    except AssertionError as error:
        raise UserWarning("Use --proofs to specify a proof directory "
                          "(containing .litani_cache_dir)") from error

def validate_commits(commits):
    logging.debug("--commits = %s", commits)
    try:
        assert isinstance(commits, list)
        assert len(commits) == 2
        return commits
    except AssertionError as error:
        raise UserWarning("Use --commits to specify two commits or branches to compare") from error

def validate_reports(reports, commits, force):
    logging.debug("--reports = %s", reports)
    reports = reports or []
    assert isinstance(reports, list)

    if len(reports) == 0:
        assert isinstance(commits, list) and len(commits) == 2
        reports = [f'/tmp/reports/{commits[0]}', f'/tmp/reports/{commits[1]}']
    if len(reports) != 2:
        raise UserWarning("Use --reports to specify two report directories.")
    if reports[0] == reports[1]:
        reports = [f"{reports[0]}1", f"{reports[0]}2"]

    if os.path.exists(reports[0]) and not force:
        raise UserWarning(f"Path {reports[0]} exists: use --force to overwrite")
    if os.path.exists(reports[1]) and not force:
        raise UserWarning(f"Path {reports[1]} exists: use --force to overwrite")

    return reports

def validate_installs(installs, commits, force):
    logging.debug("--installs = %s", installs)
    installs = installs or []
    assert isinstance(installs, list)

    if len(installs) == 0:
        assert isinstance(commits, list) and len(commits) == 2
        installs = [f'/tmp/viewer/{commits[0]}', f'/tmp/viewer/{commits[1]}']
    if len(installs) != 2:
        raise UserWarning("Use --installs to specify two install directories.")
    if installs[0] == installs[1]:
        installs = [f"{installs[0]}1", f"{installs[0]}2"]

    if os.path.exists(installs[0]) and not force:
        raise UserWarning(f"Path {installs[0]} exists: use --force to overwrite")
    if os.path.exists(installs[1]) and not force:
        raise UserWarning(f"Path {installs[1]} exists: use --force to overwrite")

    return installs

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
    configure_logging(args.verbose, args.debug)
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
