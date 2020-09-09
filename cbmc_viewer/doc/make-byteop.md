# Name

make-byteop -- list all byte extract and update operations

# Synopsis

	usage: make-byteop [-h] [--byteop FILE] [--srcdir SRCDIR]
					   [--reportdir REPORTDIR] [--verbose] [--debug]

# Description

This is a front end for the byteopt module that viewer uses to scan
the results of cbmc byte extract/update metric collection. The output is a json file that describes the SSA expression and source location corresponding to an extract or update along with the total number of extract/update operations.

Simple uses of make-byteop are

	# Generate the byte op metric data from output of "cbmc --show-byte-ops"
	# cbmc --show-byte-ops --json-ui program.goto > byteops.json
	make-byteop --byteop byteops.json --srcdir /usr/project --reportdir html_report_dir

Type "make-byteop --help" for a complete list of command line options.
