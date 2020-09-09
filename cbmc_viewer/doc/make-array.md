# Name

make-array -- list count and type of array constraints added during CBMC postprocessing

# Synopsis

	usage: make-array [-h] [--array FILE] [--reportdir REPORTDIR] 
                      [--verbose] [--debug]

# Description

This is a front end for the arrayt module that viewer uses to scan
the results of cbmc array constraint metric collection. The output 
is a json file that describes the type and count of array constraints
added by cbmc during postprocessing.

Simple uses of make-array are

    # Generate the array constraint data from output of "cbmc --show-array-constraints"
    # cbmc --show-array-constraints --json-ui program.goto > array.json
    make-array --array array.json --reportdir html_report_dir

Type "make-array --help" for a complete list of command line options.
