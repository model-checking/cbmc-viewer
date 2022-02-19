# Name

make-property -- list the properties checked by cbmc during property checking

# Synopsis

	usage: make-property [-h] [--viewer-property JSON [JSON ...]]
						 [--srcdir SRCDIR] [--verbose] [--debug]
						 [cbmc_property [cbmc_property ...]]

# Description

This is a front end for the propertyt module that viewer uses to
generate the list of properties checked by cbmc during property checking. The
output is a json file that maps each property to a property
description and a source location consisting of a file name, optional
function name, and line number.

Simple uses of make-property are

    # Load the list of properties from a json file produced by make-property
    make-property --viewer-property property.json

    # Generate the list of properties from cbmc output
    # cbmc --show-properties --json-ui $FLAGS program.goto > property.json
    # cbmc --show-properties --xml-ui $FLAGS program.goto > property.xml
    make-property --srcdir /usr/project property.json
    make-property --srcdir /usr/project property.xml

In both cases, you can supply multiple json or xml files, and
make-property will combine the multiple lists into a single list.
Unlike other commands like make-loop, you cannot generate the list of
properties directly from the goto binary, because the properties
checked depend on the `$FLAGS` given to cbmc.

Type "make-property --help" for a complete list of command line options.
