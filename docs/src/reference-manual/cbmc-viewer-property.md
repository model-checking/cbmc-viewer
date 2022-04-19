# Reference manual

## Name

`cbmc-viewer property` - List properties checked for during property checking

## Synopsis

```
cbmc-viewer property [-h] [--property FILE [FILE ...]]
                          [--srcdir SRCDIR]
                          [--viewer-property JSON [JSON ...]] [--verbose]
                          [--debug] [--version]
```

## Description

List properties checked for during property checking

## Options

### CBMC output

This is the output of CBMC that is summarized by cbmc-viewer. Output can
be text, xml, or json, but xml is strongly preferred.

`--property FILE [FILE ...]`

* CBMC properties checked during property checking. The output of "cbmc --show-properties".

### Source files

`--srcdir SRCDIR`

* The root of the source tree, typically the root of the code repository.

### Viewer input

Load json output of cbmc-viewer like "viewer-coverage.json" or the output
of cbmc-viewer subcommands like "cbmc-viewer coverage".

`--viewer-property JSON [JSON ...]`

* Load the output of "cbmc-viewer" or "cbmc-viewer
  property" listing the properties checked during CBMC
  property checking.

### Other

`--help`

`--verbose`

* Verbose output.

`--debug`

* Debugging output.

`--version`

* Display version number and exit.
