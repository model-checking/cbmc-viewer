This is the visible-steps unit test for cbmc-viewer: Run "make".

CBMC marks some steps in the xml and json representation of an error
trace as hidden.  A hidden step is generally an internal step of CBMC
that is of no interest to a user debugging a code issue raised by
CBMC, but there are two exceptions:

* Function invocations and returns should be visible.  CBMC marks
  malloc invocation as visible and return as hidden.

* Initialization of static data should be visible.  CBMC marks
  assignments initializing static data within CBMC initialization as
  hidden.

[Pull request 76](https://github.com/awslabs/aws-viewer-for-cbmc/pull/76)
makes this adjustment, and this unit test is an example.
