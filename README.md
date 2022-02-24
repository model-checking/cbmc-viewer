## CBMC Viewer

[CBMC](https://github.com/diffblue/cbmc) is a Bounded Model Checker for C.
It can prove that (for computations of bounded depth) a C program exhibits
no memory safe errors (no buffer overflows, no invalid pointers, etc),
no undefined behaviors, and no failures of assertions in the code.
[CBMC Viewer](https://github.com/awslabs/aws-viewer-for-cbmc) is a tool
that scans the output of CBMC and produces a browsable summary of its findings.

## Example

Here is a simple example of using cbmc-viewer.
Running this example requires installing [CBMC](https://github.com/diffblue/cbmc).
Installation on MacOS is just `brew install cbmc`.
Installation on other operation systems is described on the [CBMC
release page](https://github.com/diffblue/cbmc/releases/latest).

Create a source file `main.c` containing
```
#include <stdlib.h>

static int global;

int main() {
  int *ptr = malloc(sizeof(int));

  assert(global > 0);
  assert(*ptr > 0);

  return 0;
}
```
and run the commands
```
goto-cc -o main.goto main.c
cbmc main.goto --trace --xml-ui > result.xml
cbmc main.goto --cover location --xml-ui > coverage.xml
cbmc main.goto --show-properties --xml-ui > property.xml
cbmc-viewer --goto main.goto --result result.xml --coverage coverage.xml --property property.xml --srcdir .
```
and open the report created by cbmc-viewer in a web browser with
```
open report/html/index.html
```

What you will see is

* A *coverage report* summarizing what lines of source code were
  exercised by cbmc.  In this case, coverage is 100%.  Clicking on `main`,
  you can see the source code for `main` annotated with coverage data
  (all lines are green because all lines were hit).

* A *bug report* summarizing what issues cbmc found with the code. In this case,
  the bugs are violations of the assertions because, for example, it is possible
  that the uninitialized integer allocated on the heap contains a negative value.
  For each bug, there is a link to

    * The line of code where the bug occurred.

    * An error trace showing the steps of the program leading to the bug.
      For each step, there a link to the line of code that generated the step,
      making it easy to follow the error trace and root cause the bug.

## Tools

This package provides a set of command-line tools that scan the
verification artifacts produced by CBMC to answer interesting
questions like "What are the results of the property checking?"
(`make-result`) and "What are the results of the coverage checking?"
(`make-coverage`) and "What are the error traces discovered?"
(`make-trace`). The answer to each question is given in the form of a
json blob that summarizes the answer.

This package provides a command line tool `cbmc-viewer` that renders
the answers to these questions into a set of web pages that can be
opened in a web browser and studied to understand and debug CBMC findings.  By
default, `cbmc-viewer` runs the various `make-*` tools itsef before
rendering the results.  Other tools can use the `make-*` tools to do
other analysis.  For example, a different tool could combine the results
of all proofs in a project into a single project summary, or could render the
results within a integrated development environment.

For more information, see cbmc-viewer

* [cbmc-viewer](https://github.com/awslabs/aws-viewer-for-cbmc/blob/master/src/cbmc_viewer/doc/cbmc-viewer.md)

and the supporting command-line tools

* [make-coverage](https://github.com/awslabs/aws-viewer-for-cbmc/blob/master/src/cbmc_viewer/doc/make-coverage.md)
* [make-loop](https://github.com/awslabs/aws-viewer-for-cbmc/blob/master/src/cbmc_viewer/doc/make-loop.md)
* [make-property](https://github.com/awslabs/aws-viewer-for-cbmc/blob/master/src/cbmc_viewer/doc/make-property.md)
* [make-reachable](https://github.com/awslabs/aws-viewer-for-cbmc/blob/master/src/cbmc_viewer/doc/make-reachable.md)
* [make-result](https://github.com/awslabs/aws-viewer-for-cbmc/blob/master/src/cbmc_viewer/doc/make-result.md)
* [make-source](https://github.com/awslabs/aws-viewer-for-cbmc/blob/master/src/cbmc_viewer/doc/make-source.md)
* [make-symbol](https://github.com/awslabs/aws-viewer-for-cbmc/blob/master/src/cbmc_viewer/doc/make-symbol.md)
* [make-trace](https://github.com/awslabs/aws-viewer-for-cbmc/blob/master/src/cbmc_viewer/doc/make-trace.md)

For all commands, the --help option prints detailed documentation of
the command line arguments, and the --verbose and --debug options may
help figure out what is going on when something unexpected happens.

## Installation

Most people should just follow the instructions on the
[release page](https://github.com/awslabs/aws-viewer-for-cbmc/releases/latest).

Developers can install the package in Python "development mode" as follows.
First, follow the instructions on the
[release page](https://github.com/awslabs/aws-viewer-for-cbmc/releases/latest) to install the dependencies,
then

* Clone the repository with
  ```
      git clone https://github.com/awslabs/aws-viewer-for-cbmc.git cbmc-viewer
  ```
* Install development mode with
  ```
      cd cbmc-viewer
      make develop
      export PATH=$(pwd):$PATH
  ```
* Uninstall development mode with
  ```
      cd cbmc-viewer
      make undevelop
  ```

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.
