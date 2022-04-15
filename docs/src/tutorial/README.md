# Tutorial

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
