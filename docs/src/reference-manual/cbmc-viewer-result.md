# Reference manual

## Name

`cbmc-viewer result` - Summarize CBMC property checking results

## Synopsis

```
cbmc-viewer result [-h] [--result FILE [FILE ...]]
                        [--viewer-result JSON [JSON ...]] [--verbose]
                        [--debug] [--version]
```

## Description

Summarize CBMC property checking results

## Options

### CBMC output

This is the output of CBMC that is summarized by cbmc-viewer. Output can
be text, xml, or json, but xml is strongly preferred.

`--result FILE [FILE ...]`

* CBMC property checking the results. The output of "cbmc".

### Viewer input

Load json output of cbmc-viewer like "viewer-coverage.json" or the output
of cbmc-viewer subcommands like "cbmc-viewer coverage".

`--viewer-result JSON [JSON ...]`

* Load the output of "cbmc-viewer" or "cbmc-viewer result" giving the CBMC property checking results.

### Other

`--help`

`--verbose`

* Verbose output.

`--debug`

* Debugging output.

`--version`

* Display version number and exit.
