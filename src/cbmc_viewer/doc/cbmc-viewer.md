# Name

cbmc-viewer -- assemble a browsable summary of cbmc results

# Synopsis

	usage: cbmc-viewer [-h] [--result FILE [FILE ...]]
					   [--coverage FILE [FILE ...]] [--property FILE [FILE ...]]
					   [--srcdir SRCDIR] [--exclude EXCLUDE] [--extensions REGEXP]
					   [--source-method MHD] [--tags-method TAGS] [--wkdir WKDIR]
					   [--goto GOTO] [--reportdir REPORTDIR] [--json-summary JSON]
					   [--viewer-coverage JSON [JSON ...]]
					   [--viewer-loop JSON [JSON ...]]
					   [--viewer-property JSON [JSON ...]]
					   [--viewer-reachable JSON [JSON ...]]
					   [--viewer-result JSON [JSON ...]]
					   [--viewer-source JSON [JSON ...]]
					   [--viewer-symbol JSON [JSON ...]]
					   [--viewer-trace JSON [JSON ...]] [--verbose] [--debug]
					   [--config JSON] [--version]

# Description

CBMC viewer scans the output of CBMC and produces a browsable summary of the
artifacts produced by CBMC in the form of a collection of html pages.

A simple use of cbmc-viewer is

    # Generate the list of source files used to build the goto binary
    make-source --srcdir /usr/project --wkdir /usr/project/cbmc > sources.json

	# Build the goto binary main.goto
	make goto

	# Do cbmc property checking
	cbmc $FLAGS --unwinding-assertions --xml-ui main.goto > result.xml

	# Do cbmc coverage checking
	cbmc $FLAGS --cover location --xml-ui main.goto > coverage.xml

	# List properties checked during property checking
	cbmc $FLAGS --unwinding-assertions --show-properties --xml-ui main.goto > \
	    property.xml

	# Run cbmc-viewer
	cbmc-viewer \
	  --viewer-source sources.json \
	  --goto main.goto \
	  --srcdir /usr/project \
	  --result result.xml \
	  --property property.xml \
	  --coverage coverage.xml

	# Open the report in a browser
    open report/html/index.html

Type "cbmc-viewer --help" for a complete list of command line options.
