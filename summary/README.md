This directory contains a script that scans the viewer output for a
set of and produce a summary of the stubs and undefined functions
being used in the proofs.  This is a work-in-progress.

* projects.json is a list of projects on gitub.  Each entry gives the
  url for the github repository and the path within the repository to
  the cbmc proofs.  See more below.

* summary.py scans the list of projects and clones the repositories,
  runs the proofs, summarizes the results, and produces a table of the
  results.  See `summary.py --help`.

* stubs.py summarizes the stubs and undefined functions used in a proof.
  It is used as a library by summary.py, but see `stubs.py --help`.

Here is an example of a project list:

```
projects.json:
    {
      "Baseball": {
        "github": "https://github.com/johnqpublic/baseball-fantasy-team.git",
        "proofs": "tools/cbmc/proofs"
      },
      "Football": {
        "github": "https://github.com/johnqpublic/football-fantasy-team.git",
        "proofs": "test/cbmc/proofs"
      }
    }
```

This list describes two projects named "Baseball" and "Football".  For
"Baseball",

* `https://github.com/johnqpublic/baseball-fantasy-team.git` is the
  URL for the code repository, and
* `tools/cbmc/proofs` is the path within the repository to the
  directory under which all of the CBMC proofs can be found.

Similarly for "Football". The names "Baseball" and "Football" are just
short names for the projects.  They are used to refer the the projects
on the command line with `summary.py --project Baseball Football` and
they are used as column headers for the projects in the spreadsheet
produced by `summary.py --chart`.
