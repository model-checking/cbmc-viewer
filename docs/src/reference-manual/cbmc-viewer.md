# Reference manual

## Name

`cbmc-viewer` - Generate a browsable summary of CBMC results

## Synopsis

```
cbmc-viewer [-h] [--result FILE [FILE ...]]
                 [--coverage FILE [FILE ...]] [--property FILE [FILE ...]]
                 [--srcdir SRCDIR] [--exclude EXCLUDE] [--extensions REGEXP]
                 [--source-method MHD] [--wkdir WKDIR] [--goto GOTO]
                 [--reportdir REPORTDIR] [--json-summary JSON]
                 [--viewer-coverage JSON [JSON ...]]
                 [--viewer-loop JSON [JSON ...]]
                 [--viewer-property JSON [JSON ...]]
                 [--viewer-reachable JSON [JSON ...]]
                 [--viewer-result JSON [JSON ...]]
                 [--viewer-source JSON [JSON ...]]
                 [--viewer-symbol JSON [JSON ...]]
                 [--viewer-trace JSON [JSON ...]] [--verbose] [--debug]
                 [--config JSON] [--version] [--block BLOCK]
                 [--htmldir HTMLDIR] [--srcexclude EXCLUDE]
                 [--blddir BLDDIR] [--storm STORM]
```

## Description

CBMC Viewer generates a browsable summary of CBMC results that makes it
easy to root cause issues found by CBMC.

## Options

### CBMC output

This is the output of `cbmc` that is summarized by `cbmc-viewer`.

The output of `cbmc` can be text, xml, or json.  `cbmc` outputs text
by default, but `cbmc --xml-ui` and `cbmc --json-ui` will output xml
and json instead.  `cbmc-viewer` can generally accept output in any
form, but xml is strongly preferred.

The output of `cbmc-viewer` can be a summary of multiple invocations
of `cbmc`.  For example, after testing one function with `cbmc` in
multiple configurations, invoking `cbmc-viewer` with the results of
all of these tests in all of these configurations will generate a
single report summarizing the union of these results.


`--result FILE [FILE ...]`

* The property checking results. A text, xml, or json file containing
  the output of `cbmc`.

`--coverage FILE [FILE ...]`

* The coverage checking results. An xml or json file containing the
  output of `cbmc --cover locations`.

`--property FILE [FILE ...]`

* The properties checked during property checking. An xml or json
  file containing the output of `cbmc --show-properties`.

### Source files

`--srcdir SRCDIR`

* The root of the source tree.  This is typically the root of the code
  repository itself. For best results, the source tree should include
  both the project code and the proof code written to facilitate
  verification (for example, stubs for functionality not
  being tested).  The final report will not link to files outside the
  source tree or to symbols defined in files outside the source tree.

`--exclude EXCLUDE`

* A regular expression for the paths relative to SRCDIR to exclude from
  the list of source files.  This is rarely used.  It is a Python regular
  expression matched against the result of os.path.normpath(). The
  match is case insensitive.

`--extensions REGEXP`

* A regular expression for the file extensions of files to include
  in the list of source files.  This is rarely used.  It is a Python regular
  expression matched against the result of os.path.splitext(). The
  match is case insensitive. (Default: `^\.(c|h|inl)$`)

`--source-method MHD`

* The method to use to enumerate the list of source files. This is
  rarely used.  The default method is generally to use the files
  mentioned in the symbol table of the goto binary.  The full set of
  methods available is

    * `find`: use the Linux `find` command in SRCDIR,
    * `walk`: use the Python `walk` method in SRCDIR,
    * `make`: use the `make` command in the WKDIR to build the goto
       binary with the preprocessor and use the files under SRCDIR
       mentioned in the preprocessor output, and
    * `goto`: use the files under SRCDIR mentioned in the symbol table
      of the goto binary.

  The default method is `goto` if SRCDIR and
  WKDIR and GOTO are specified, `make` if SRCDIR and WKDIR are
  specified, `walk` on Windows, and `find` otherwise.

### Goto binaries

`--wkdir WKDIR`

* The working directory.  This is generally the directory in which
  `goto-cc` was invoked to build the goto binary.  It is the working
  directory that is mentioned in the source locations in the goto
  binary.  It is used to resolve relative paths appearing in source
  locations into absolute paths to source files.  Relative paths
  appear in source locations only when `goto-cc` is invoked with
  relative paths.  If `goto-cc` is invoked with absolute paths, paths
  in source locations are absolute paths, and this working directory
  is not needed.

`--goto GOTO`

* The goto binary itself.

### Viewer output

`--reportdir REPORTDIR`

* The report directory. Write the final report to this
  directory. (Default: report)

`--json-summary JSON`

* Write summary of key metrics to this json file.

### Viewer input

JSON files produced by the various make-* scripts.


`--viewer-coverage JSON [JSON ...]`

* Load coverage data from the JSON output of make-coverage. If
                      multiple files are given, merge multiple data
                      sets into one.

`--viewer-loop JSON [JSON ...]`

* Load loops from the JSON output of make-loop. If multiple files are
  given, merge multiple data sets into one.

`--viewer-property JSON [JSON ...]`

* Load properties from the JSON output of make-property.  If multiple
  files are given, merge multiple data sets into one.

`--viewer-reachable JSON [JSON ...]`

* Load reachable functions from the JSON output of make-reachable. If
  multiple files are given, merge multiple data sets into one.

`--viewer-result JSON [JSON ...]`

* Load results from the JSON output of make-result. If multiple files
  are given, merge multiple data sets into one.

`--viewer-source JSON [JSON ...]`

* Load sources from the JSON output of make-source. If multiple files
  are given, merge multiple data sets into one.

`--viewer-symbol JSON [JSON ...]`

* Load symbols from the JSON output of make-symbol. If multiple files
  are given, merge multiple data sets into one.

`--viewer-trace JSON [JSON ...]`

* Load traces from the JSON output of make-trace. If multiple files
  are given, merge multiple data sets into one.

### Other


`--help, -h`

`--verbose`

* Verbose output.

`--debug`

* Debugging output.

`--config JSON`

* JSON configuration file. (Default: `cbmc-viewer.json`)

`--version`

* Display version number and exit.

### Deprecated:

Options from prior versions now deprecated.

`--block BLOCK`

* Use --coverage instead.

`--htmldir HTMLDIR`

* Use --reportdir instead.

`--srcexclude EXCLUDE`

* Use --exclude instead.

`--blddir BLDDIR`

* Ignored.

`--storm STORM`

* Ignored.
