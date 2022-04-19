# Reference manual

## Name

`cbmc-viewer coverage` - Summarize coverage checking results

## Synopsis

```
cbmc-viewer coverage [-h] [--coverage FILE [FILE ...]]
                          [--srcdir SRCDIR]
                          [--viewer-coverage JSON [JSON ...]] [--verbose]
                          [--debug] [--version]
```

## Description

Summarize coverage checking results

## Options

### CBMC output

This is the output of CBMC that is summarized by cbmc-viewer. Output can
be text, xml, or json, but xml is strongly preferred.

`--coverage FILE [FILE ...]`

* CBMC coverage checking results. The output of "cbmc --cover locations".

### Source files

`--srcdir SRCDIR`

* The root of the source tree, typically the root of the code repository.

### Viewer input

Load json output of cbmc-viewer like "viewer-coverage.json" or the output
of cbmc-viewer subcommands like "cbmc-viewer coverage".

`--viewer-coverage JSON [JSON ...]`

* Load the output of "cbmc-viewer" or "cbmc-viewer coverage" giving CBMC coverage checking results.

### Other

`--help`

`--verbose`

* Verbose output.

`--debug`

* Debugging output.

`--version`

* Display version number and exit.
