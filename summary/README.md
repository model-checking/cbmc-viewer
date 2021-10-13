This directory contains a script that scans the viewer output for a
set of and produce a summary of the stubs and undefined functions
being used in the proofs.  This is a work-in-progress.

* projects.json is a list of projects on gitub.  Each entry gives the
  url for the github repository and the path within the repository to
  the cbmc proofs.

* summary.py scans the list of projects and clones the repositories,
  runs the proofs, summarizes the results, and produces a table of the
  results.  See `summary.py --help`.

* stubs.py summarizes the stubs and undefined functions used in a proof.
  It is used as a library by summary.py, but see `stubs.py --help`.
