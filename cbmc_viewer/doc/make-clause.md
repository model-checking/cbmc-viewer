# Name

make-clause -- list solver query complexity metrics

# Synopsis

	usage: make-clause [-h] [--clause FILE] [--srcdir SRCDIR] 
                        --dimacs DIMACS --core CORE [--verbose]
                       [--debug]

# Description

This is a front end for the clauset module that viewer uses to scan
the results of cbmc solver query complexity metric collection. The
output is a json file that describes a mapping between clauses and 
lines of program code. Additionally, it highlights instructions that
contribute to the UNSAT core and also program locations that do not 
contribute any clauses to the UNSAT core.

Simple uses of make-clause are

    # Generate the list of solver query complexity metric from output of 
    # "cbmc --write-solver-stats-to"
    # cbmc --write-solver-stats-to clause.json program.goto
    # Generate dimacs cnf formula 
    # cbmc program.goto --dimacs --outfile dimacs.cnf
    # Extract UNSAT core
    # kissat dimacs.cnf proof
    # drat-trim dimacs.cnf proof -c core
    make-clause --clause clause.json --dimacs dimacs.cnf --core core 
    --srcdir /usr/project

Type "make-clause --help" for a complete list of command line options.
