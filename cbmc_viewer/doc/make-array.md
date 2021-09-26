# Name

make-array -- list all array constraint metrics

# Synopsis

	usage: make-array [-h] [--array FILE] [--verbose] [--debug]

# Description

This is a front end for the arrayt module that viewer uses to scan
the results of cbmc array constraint metric collection. The output
is a json file that describes the type and count of array constraints
added by cbmc during postprocessing.

Simple uses of make-array are

    # Generate the list of array constraint metrics from output of
    # "cbmc --show-array-constraints"
    # cbmc --show-array-constraints --json-ui program.goto > array.json
    make-array --array array.json

Type "make-array --help" for a complete list of command line options.
