# Getting started with CBMC viewer

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

## Installation

Most people should just follow the instructions on the
[release page](https://github.com/awslabs/aws-viewer-for-cbmc/releases/latest).

Developers can install the package in Python "development mode" as follows.
First, follow the instructions on the
[release page](https://github.com/model-checking/cbmc-viewer/releases/latest)
to install the dependencies.  Then,

* Clone the repository with
  ```
  git clone https://github.com/model-checking/cbmc-viewer cbmc-viewer
  ```
* Install development mode with
  ```
  cd cbmc-viewer
  make develop
  export PATH=$PATH:$(pwd)
  ```
* Uninstall development mode with
  ```
  cd cbmc-viewer
  make undevelop
  ```

## Helping others

This training material is a work in progress.  If you have suggestions,
corrections, or questions, contact us by submitting a
[GitHub issue](https://github.com/model-checking/cbmc-viewer/issues).
If you have some training of your own that you would like to contribute,
submit your contributions as a
[GitHub pull request](https://github.com/model-checking/cbmc-viewer/pulls).
