# Name

make-coverage -- list the results of coverage checking

# Synopsis

	usage: make-coverage [-h] [--viewer-coverage JSON [JSON ...]]
						 [--srcdir SRCDIR] [--verbose] [--debug]
						 [cbmc_coverage [cbmc_coverage ...]]

# Description

This is a front end for the coveraget module that viewer uses to scan
the results of cbmc coverage checking. The output is a json file that
describes the coverage obtained by cbmc.

Simple uses of make-coverage are

    # Load the coverage data from a json file produced by make-coverage
    make-coverage --viewer-coverage coverage.json

    # Generate the coverage data from output of "cbmc --cover location"
    # cbmc --cover location --json-ui program.goto > coverage.json
    # cbmc --cover location --xml-ui program.goto > coverage.xml
    make-coverage --srcdir /usr/project coverage.json
    make-coverage --srcdir /usr/project coverage.xml

If you supply multiple json or xml files, make-coverage will combine
the coverage data into a single coverage summary.

Type "make-coverage --help" for a complete list of command line options.
