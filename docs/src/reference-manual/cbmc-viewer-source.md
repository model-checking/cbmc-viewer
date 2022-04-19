# Reference manual

## Name

`cbmc-viewer source` - List source files used to build the goto binary

## Synopsis

```
cbmc-viewer source [-h] [--srcdir SRCDIR] [--exclude EXCLUDE]
                        [--extensions REGEXP] [--source-method MHD]
                        [--wkdir WKDIR] [--goto GOTO]
                        [--viewer-source JSON [JSON ...]] [--verbose]
                        [--debug] [--version]
```

## Description

List source files used to build the goto binary

## Options

### Source files

`--srcdir SRCDIR`

* The root of the source tree, typically the root of the code repository.

`--exclude EXCLUDE`

* A regular expression for the paths relative to SRCDIR to exclude from the list of source files. This is rarely used.

`--extensions REGEXP`

* A regular expression for the file extensions of files to include in the list of source files. This is rarely used.
  (Default: ^\.(c|h|inl)$)

`--source-method MHD`

* The method to use to enumerate the list of source
  files. This is rarely used. The default method 'goto'
  is generally to use the files mentioned in the symbol
  table of the goto binary. The full set of methods
  available is
  * 'find': use the Linux 'find' command in SRCDIR,
  * 'walk': use the Python 'walk' method in SRCDIR,
  * 'make': use the 'make' command in the WKDIR to build the goto binary with the preprocessor and use the files under SRCDIR mentioned in the preprocessor output, and
  * 'goto': use the files under SRCDIR mentioned in the symbol table of the goto binary.

### GOTO binaries

`--wkdir WKDIR  `

* The working directory. This is generally the directory
  in which `goto-cc` was invoked to build the goto
  binary. It is the working directory that is mentioned
  in the source locations in the goto binary.

`--goto GOTO`

* The goto binary itself.

### Viewer input

Load json output of cbmc-viewer like "viewer-coverage.json" or the output
of cbmc-viewer subcommands like "cbmc-viewer coverage".

`--viewer-source JSON [JSON ...]`

* Load the output of "cbmc-viewer" or "cbmc-viewer
  source" listing the source files used to build the
  goto binary.

### Other

`--help`

`--verbose`

* Verbose output.

`--debug`

* Debugging output.

`--version`

* Display version number and exit.
