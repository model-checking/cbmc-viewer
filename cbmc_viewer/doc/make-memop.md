# Name

make-memop -- list all calls to memory operations

# Synopsis

	usage: make-memop [-h] [--memop FILE] [--srcdir SRCDIR]
					  [--verbose] [--debug]

# Description

This is a front end for the memopt module that viewer uses to scan
the results of cbmc memory operation call metric. The output is a 
json file that describes the function call and location for memory 
operations like memcpy, memset, memchr, memmove etc.

Simple uses of make-memop are

    # Generate the list of memop calls from output of
    # "cbmc --show-goto-functions"
    # cbmc --show-goto-functions --json-ui program.goto > memop.json
    make-memop --memop memop.json --srcdir /usr/project

Type "make-memop --help" for a complete list of command line options.
