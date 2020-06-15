# Name

make-reachable -- list the reachable functions in a goto binary

# Synopsis

    usage: make-reachable [-h] [--viewer-reachable JSON [JSON ...]]
                          [--goto GOTO]
                          [--srcdir SRCDIR] [--verbose] [--debug]
                          [cbmc_reachable [cbmc_reachable ...]]


# Description

This is a front end for the reachablet module that viewer uses to
generate the list of reachable functions in a goto binary. The output is a json
file that lists files and reachable functions within the file.

Simple uses of make-reachable are

    # Load the reachable functions from a json file produced by make-reachable
    make-reachable --viewer-reachable reachable.json

    # Generate the reachable functions from the goto binary itself
    make-reachable --goto program.goto --srcdir /usr/project

    # Generate the list of reachable functions from goto-analyzer output
    # goto-analyzer --reachable-functions --json - program.goto > reachable.json
    # goto-analyzer --reachable-functions --xml - program.goto > reachable.xml
    make-reachable --srcdir /usr/project reachable.json
    make-reachable --srcdir /usr/project reachable.xml

In the first and third uses, you can supply multiple json or xml files,
and make-reachable will combine the multiple lists into a single list.
At the moment, however, xml output of goto-analyzer is text and not xml
and will not be parsed by make-reachable.

Type "make-reachable --help" for a complete list of command line options.
