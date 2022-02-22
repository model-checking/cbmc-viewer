The script makes it easy to compare two versions of cbmc-viewer.

A common use case is that we have two versions of cbmc-viewer in branches
names master and bugfix, and we want to see how the output of the two
versions differ on a set of proofs built using litani as we do with the
starter kit.

* Checkout the repository.  Make the output of cbmc-viewer interesting
  by deleting some proof assumptions to break the proofs.  Run the
  proofs with run-cbmc-proofs.py (or some subset of the proofs using the
  script's --proof command line argument) in /repo/test/cbmc/proofs.

* Run
  ```
  difference.py \\
     --viewer-repository . \\
     --proofs /repo/test/cbmc/proofs \\
     --commits master bugfix \\
     --litani /repo/test/cbmc/proofs/litani/litani
  ```
  to run the two versions master and bugfix of cbmc-viewer on the
  output of cbmc on the proofs in /repo/test/cbmc/proofs, and to write
  the proof reports into the directories /tmp/reports/master and
  /tmp/reports/bugfix.

* Run
  ```
  diff -r /tmp/reports/master /tmp/reports/bugfix
  ```
  to compare the results.

In the simple case, where the difference between master and bugfix is
just code clean-up, there is no actual difference in the output of
cbmc-viewer and the diff will be clean.

In the common case, however, there will be some difference.  Perhaps
the json summary of the traces differ in that some of the steps in the
trace that are internal to cbmc are now omitted.  In this case, the
output of diff may be hard to read, but some simple queries with jq
may be able to confirm that the changes are as desired.

The script works as follows:

* For each branch master and bugfix, create python virtual environments
  /tmp/viewer/master and /tmp/viewer/bugfix, check out the versions master
  and bugfix, and install them into the corresponding virtual environments.

* Load the run.json summary produced by the litani build of the proofs
  and extract the jobs that invoked cbmc-viewer

* Reconstruct the 'litani add-job' commands the added these cbmc-viewer
  jobs to the build.

* Modify these add-job commands to produce two sets of add-job
  commands: One set invokes the cbmc-viewer in /tmp/viewer/master and
  writes the reports into /tmp/reports/master, and the other set does
  the same for bugfix.

* Now issue litani init, these new litani add-jobs, and finally litani
  run-build.

This script solves the following problem with writing unit tests for
cbmc-viewer.

* First, the input to cbmc-viewer is too big to store in the
  repository.  Generating interesting output with cbmc-viewer requires
  having interesting proofs for cbmc to analyze, and size of the code
  and size of the cbmc output is too big to store in a repository.

* Second, the expected output of cbmc-viewer is too big to store in
  the repository.  Generating interesting output with cbmc-viewer
  generates a lot of output.  The json output itself can be several
  megabytes.

Even if we did store this in the repository, no one would want to code
review changes to the data as cbmc-viewer changes.

This method lets us use existing proof repositories for unit tests,
use the output of an existing version of cbmc-viewer like master as
the expected output, and compare that with the output of a new version
like bugfix.  This makes it easy to test during development, and makes
it possible to test in continuous integration by comparing the HEAD
with the branch we want to merge into HEAD.