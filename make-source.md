# Name

make-source -- list source files used to build a goto binary

# Synopsis

	usage: make-source [-h] [--viewer-source JSON [JSON ...]] [--goto GOTO]
					   [--srcdir SRCDIR] [--wkdir WKDIR] [--source-method MHD]
					   [--extensions REGEXP] [--exclude EXCLUDE] [--verbose]
					   [--debug]

# Description

This is a front end for the sourcet module that viewer uses to
represent the list of source files used to build a goto binary.  The
output is a json file that gives the source root, a list of source
files under the source root, and a complete list of source files that
may even include system include files.

The are four methods of generating the list of source files:

* *source*: Load the json output of make-source itself
* *find*: Use the find command to list the sources under the source root.
* *walk*: Use walk method from Python to list the sources under the source root.
* *goto*: Use the files listed in the symbol table of the goto binary.
* *make*: Use the invocation of make used to build the goto binary
  with goto-cc in the first place, but run goto-cc as a preprocessor,
  and extract the names of source files appearing in the preprocessed
  output.

Simple uses of make-source are

	# Load a json file
	make-source --viewer-source source.json

	# Load file listed in the symbol table of the goto binary
	make-source --srcdir /usr/project  --wkdir /usr/project/cbmc --goto pgm.goto

	# Run find under /usr/project (run walk on Windows)
	make-source --srcdir /usr/project

	# Run make in /usr/project/cbmc with root /usr/project
	make-source --srcdir /usr/project --wkdir /usr/project/cbmc

	# Explicitly specify the method to use
	make-source --srcdir /usr/project --source-method find
	make-source --srcdir /usr/project --source-method walk
	make-source --srcdir /usr/project --wkdir /usr/project/cbmc --source-method make

The *find* method is not available on Windows. The Python *walk*
method is available on all platforms, but walk is known to be slower
than find (because it stats each file). Unless otherwise specified, make-source
will choose find over walk if it is available.

The *find* and *walk* methods can generate extremely long lists of
files. Uninteresting paths can be excluded from the list by specifying
a Python regular expression for the paths under the source root to
exclude:

	make-source --srcdir /usr/project --exclude 'vendors|demos'

will exclude all paths begining with /usr/project/vendors and
/usr/project/demos. Source files can be specified with a Python
regular expression matching their file extensions (.c and .h by default)
as given by os.path.splitext:

	make-source --srcdir /usr/project --extensions '^\.c$'

will restrict the list of source files to files with the file extension '.c'.

The *goto* method returns the list of file appearing in the symbol
table of the goto binary.  This includes every file that contributes a
symbol like a function or type, but omits all files that contribute
only preprocessor definitions (like a list of error codes).

The *make* method results in the most precise, minimal list of source
files used to generate the goto binary.  The command

	make-source --srcdir /usr/project --wkdir /usr/project/cbmc

assumes that the command `make GOTO_CC=goto-cc goto` in
/usr/project/cbmc will build the goto binary. It works by running
goto-cc as a preprocessor with `make "GOTO_CC=goto-cc -E" goto` and
scanning the preprocessed output for names of source files.

Because the *make* method has the effect of replacing goto binary
objects with textual processor output, the command runs "make clean"
before and after running the preprocessor to clean up. For this
reason, it is imporant to run make-source before building goto
objects for cbmc: well-written dependencies in a Makefile can induce
building running goto-cc and cbmc a second time if make-source is
run afer cbmc.

Type "make-source --help" for a complete list of command line options.
