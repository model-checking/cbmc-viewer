# Name

make-trace -- list the results of trace checking

# Synopsis

	usage: make-trace [-h] [--viewer-trace JSON [JSON ...]] [--wkdir WKDIR]
					  [--srcdir SRCDIR] [--verbose] [--debug]
					  [cbmc_trace [cbmc_trace ...]]

# Description

This is a front end for the tracet module that viewer uses to scan
the results of cbmc trace checking. The output is a json file that
describes the trace obtained by cbmc.

Simple uses of make-trace are

    # Load the trace data from a json file produced by make-trace
    make-trace --viewer-trace trace.json

    # Generate the trace data from output of "cbmc --cover location"
    # cbmc --cover location --json-ui program.goto > trace.json
    # cbmc --cover location --xml-ui program.goto > trace.xml
    make-trace --srcdir /usr/project trace.json
    make-trace --srcdir /usr/project trace.xml

If you supply multiple json or xml files, make-trace will combine the
trace files into a single trace file.

Type "make-trace --help" for a complete list of command line options.
