# Reference manual

CBMC Viewer produces a browsable summary of CBMC results.

This report includes a summary of CBMC's property checking results. The
summary lists each property CBMC was able to violate along with a error trace
demonstrating the program execution CBMC discovered that violates the
property.  Each step of the error trace is linked back to the line of
source code that generated the step, making it easier to follow the error
trace through the source code and debug the issue raised by CBMC.

This report also includes a summary of the code coverage CBMC attained during
property checking.  In the process of considering all possible executions
through the code on all possible inputs, CBMC is able to exercise some lines
of code and not other others.  The code coverage summary computes the fraction of
statically reachable code that CBMC was able to exercise.  The source code
itself is annotated in the style of [gcov](https://en.wikipedia.org/wiki/Gcov)
with reachable lines colored green and unreachable lines colored red.

By default, this report is written to `report/html`.

Here is the reference manual for `cbmc-viewer`:

* [cbmc-viewer](cbmc-viewer.md)

CBMC Viewer also produces summaries that will be of no interested to
most users, but they summarize the analysis that
CBMC Viewer does to produce the main report
in the form of json files.
By default, these summaries are written to `report/json`.
For example, the file `report/json/viewer-coverage.json`
lists each line of statically-reachable source code and whether that line
was hit or missed by CBMC. It also lists for each statically-reachable
function the fraction of lines hit.
CBMC Viewer provides a collection
of subcommands that provide command-line interfaces to these analyses.
For example, the subcommand `cbmc-viewer coverage` will generate the
the json describing code coverage
that `cbmc-viewer` itself would write to `report/json/viewer-coverage.json`.

Here are the reference manuals for `cbmc-viewer` subcommands:

* [cbmc-viewer coverage](cbmc-viewer-coverage.md): Summarize coverage checking results
* [cbmc-viewer loop](cbmc-viewer-loop.md): List loops found in the goto binary
* [cbmc-viewer property](cbmc-viewer-property.md): List properties checked for during property checking
* [cbmc-viewer reachable](cbmc-viewer-reachable.md): List reachable functions in the goto binary
* [cbmc-viewer result](cbmc-viewer-result.md): Summarize property checking results
* [cbmc-viewer source](cbmc-viewer-source.md): List source files used to build the goto binary
* [cbmc-viewer symbol](cbmc-viewer-symbol.md): List symbols found in the goto binary
* [cbmc-viewer trace](cbmc-viewer-trace.md): List error traces generated for issues found during property checking
