# Name

make-result -- list the results of property checking

# Synopsis

	usage: make-result [-h] [--viewer-result JSON [JSON ...]] [--verbose]
					   [--debug]
					   [cbmc_result [cbmc_result ...]]

# Description

This is a front end for the resultt module that viewer uses to scan
the results of cbmc property checking. The output is a json file that,
among other things, lists the names of failed properties.

Simple uses of make-result are

    # Load the list of results from a json file produced by make-result
    make-result --viewer-result results.json

    # Generate the list of results from cbmc output
    # cbmc program.goto > cbmc.txt
    # cbmc --json-ui program.goto > cbmc.json
    # cbmc --xml-ui program.goto > cbmc.xml
    make-result cbmc.txt
    make-result cbmc.json
    make-result cbmc.xml

If you supply multiple text or json or xml files, make-result will
combine the results into a single list of results.

Type "make-result --help" for a complete list of command line options.
