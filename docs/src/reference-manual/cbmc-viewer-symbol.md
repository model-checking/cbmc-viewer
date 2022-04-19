# Reference manual

## Name

`cbmc-viewer symbol` - List symbols found in the goto binary

## Synopsis

```
cbmc-viewer symbol [-h] [--srcdir SRCDIR] [--wkdir WKDIR] [--goto GOTO]
                        [--viewer-source JSON [JSON ...]]
                        [--viewer-symbol JSON [JSON ...]] [--verbose]
                        [--debug] [--version]

```

## Description

List symbols found in the goto binary

## Options

### Source files

`--srcdir SRCDIR`

* The root of the source tree, typically the root of the
  code repository.

### GOTO binaries

`--wkdir WKDIR`

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

`--viewer-symbol JSON [JSON ...]`

* Load the output of "cbmc-viewer" or "cbmc-viewer symbol" listing the symbols in the goto binary.

### Other

`--help`

`--verbose`

* Verbose output.

`--debug`

* Debugging output.

`--version`

* Display version number and exit.
