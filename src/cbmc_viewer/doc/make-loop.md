# Name

make-loop -- list the loops in a goto binary

# Synopsis

	usage: make-loop [-h] [--viewer-loop JSON [JSON ...]] [--goto GOTO]
					 [--srcdir SRCDIR] [--verbose] [--debug]
					 [cbmc_loop [cbmc_loop ...]]

# Description

This is a front end for the loopt module that viewer uses to
generate the list of loops in a goto binary. The output is a json
file that maps each loop to a source location consisting of a file
name, optional function name, and line number.

Simple uses of make-loop are

    # Load the list of loops from a json file produced by make-loop
    make-loop --viewer-loop loop.json

    # Generate the list of loops from the goto binary itself
    make-loop --goto program.goto --srcdir /usr/project

    # Generate the list of loops from cbmc output
    # cbmc --show-loops --json-ui program.goto > loop.json
    # cbmc --show-loops --xml-ui program.goto > loop.xml
    make-loop --srcdir /usr/project loop.json
    make-loop --srcdir /usr/project loop.xml

In the first and third uses, you can supply multiple json or xml files,
and make-loop will combine the multiple lists into a single list.

Type "make-loop --help" for a complete list of command line options.
