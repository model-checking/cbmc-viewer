# Reference manual

## Name

`cbmc-viewer reachable` - List reachable functions in the goto binary

## Synopsis

```
cbmc-viewer reachable [-h] [--srcdir SRCDIR] [--goto GOTO]
                           [--viewer-reachable JSON [JSON ...]] [--verbose]
                           [--debug] [--version]
```

## Description

List reachable functions in the goto binary

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

`--viewer-reachable JSON [JSON ...]`

* Load the output of "cbmc-viewer" or "cbmc-viewer
  property" listing the reachable functions in the goto
  binary.

### Other

`--help`

`--verbose`

* Verbose output.

`--debug`

* Debugging output.

`--version`

* Display version number and exit.
