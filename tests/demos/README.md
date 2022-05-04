This regression test makes it easy to compare the output of two
cbmc-viewer commits on coreHTTP.

* Run `make` to compare the current branch with the master branch.

* Run `make COMMIT1=B1 COMMIT2=B2` to compare branch B1 with branch B2.
  B1 and B2 can be any commits in the repository.

In more detail:
* `make clone` will clone coreHTTP and break the proofs.
* `make build` will run the fast coreHTTP proofs and build the reports
  with the installed cbmc-viewer.
* `make compare` will rebuild the reports with the two cbmc-viewer
  commits and compare the results.
