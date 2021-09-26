# Name

make-alias -- list points-to set metrics

# Synopsis

	usage: make-alias [-h] [--alias FILE] [--verbose] [--debug]

# Description

This is a front end for the aliast module that viewer uses to scan
the results of cbmc pointer alias analysis, specifically points-to
set information. The output is a json file that describes the size
and contents of the points-to set for pointer dereferencing.

Simple uses of make-alias are

    # Generate the list points-to set metrics from output of
    # "cbmc --show-points-to-sets"
    # cbmc --show-points-to-sets --json-ui program.goto > alias.json
    make-alias --alias alias.json

Type "make-alias --help" for a complete list of command line options.
