# CBMC viewer

[CBMC](https://github.com/diffblue/cbmc) is a model checker for
C. This means that CBMC will explore all possible paths through your code
on all possible inputs, and will check that all assertions in your code are
true.
CBMC can also check for the possibility of
memory safety errors (like buffer overflow) and for instances of
undefined behavior (like signed integer overflow).
CBMC is a bounded model checker, however, which means that using CBMC may
require restricting this set of all possible inputs to inputs of some
bounded size.

[CBMC Viewer](https://github.com/model-checking/cbmc-viewer) is a tool
that scans the output of CBMC and produces a browsable summary of its findings.

* [Installation](installation)
* [Tutorial](tutorial)
* [User guide]()
* [Reference manual](reference-manual)
* [Frequently asked questions]()
* [Resources](resources)
* [Contributing](contributing)
