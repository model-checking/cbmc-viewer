# Name

make-symbol -- make a symbol table for a goto binary

# Synopsis

	usage: make-symbol [-h] [--viewer-symbol JSON [JSON ...]]
					   [--viewer-source JSON [JSON ...]] [--goto GOTO]
					   [--wkdir WKDIR] [--srcdir SRCDIR]
					   [--files FILE [FILE ...]]
					   [--tags-method TAGS] [--verbose] [--debug]

# Description

This is a front end for the symbolt module that viewer uses to
represent the symbol table for a goto binary.  The output is a json
file that maps each symbol to a source location consisting of a file
name, optional function name, and line number.

The are four methods for generating the symbol table:

* *sources*: Load the json output of make-symbol itself
* *goto*: Load the symbol table from a goto binary
* *ctags*: Use ctags to scan source code for symbols
* *etags*: Use etags to scan source code for symbols

Simple uses of make-symbol are

	# Load symbol table from a json file produced by make-symbol
	make-symbol --viewer-symbol symbols.json

	# Load symbol table from a goto binary
	make-symbol --srcdir /usr/project --wkdir /usr/project/proof \
	    --goto program.goto

	# Run ctags in SRCDIR on FILES defined in make-sources output
	make-symbol --sources sources.json

	# Run ctags in /usr/project on files function.c and .h
	make-symbol --srcdir /usr/project --files function.c function.h

	# Explicitly specify whether to use ctags or etags
	make-symbol --sources sources.json --tags-method ctags
	make-symbol --sources sources.json --tags-method etags

The goto method simply loads the symbol table found in a goto binary.
This will include every symbol used in the goto binary, but will omit
preprocessor definitions.  We fill out this list of symbols and
definitions by running ctags over the files listed in the symbol
table, but definitions in the table take precedence over definitions
inferred by ctags.  This still omits definitions from files that list
only definitions and do not contribute symbols to the symbol table.

The programs ctags and etags scan source files to produce symbol
tables that are easy to use with the vi and emacs text editors.  The
ctags method requires Exuberant ctags from ctags.sourceforge.net that
can be installed with most package managers, and the etags method
requires the version of etags distributed with any recent version of
emacs.  We prefer ctags over etags (after checking which of ctags and
etags is installed), since ctags seems more robust with
oddly-formatted source code, although etags can run twice as fast as
ctags on large source trees (as much as 30 seconds versus 60 seconds).

The goto method is easy and fairly complete.  The ctags method is both
minimal and complete when the make-sources is used to produce the file
sources.json listing files for ctags to scan.

Type "make-symbol --help" for a complete list of command line options.
