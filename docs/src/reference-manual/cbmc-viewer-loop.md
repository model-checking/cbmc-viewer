# Reference manual

## Name

`cbmc-viewer loop` - List loops found in the goto binary


## Synopsis

```
cbmc-viewer loop [-h] [--srcdir SRCDIR] [--goto GOTO]
                      [--viewer-loop JSON [JSON ...]] [--verbose] [--debug]
                      [--version]
```

## Description

List loops found in the goto binary

## Options

### Source files

`--srcdir SRCDIR`

* The root of the source tree, typically the root of the code repository.

### GOTO binaries

`--goto GOTO`

* The goto binary itself.

### Viewer input

Load json output of cbmc-viewer like "viewer-coverage.json" or the output
of cbmc-viewer subcommands like "cbmc-viewer coverage".

`--viewer-loop JSON [JSON ...]

* Load the output of "cbmc-viewer" or "cbmc-viewer loop" listing the loops found in the goto binary.

### Other

`--help`

`--verbose`

* Verbose output.

`--debug`

* Debugging output.

`--version`

* Display version number and exit.
