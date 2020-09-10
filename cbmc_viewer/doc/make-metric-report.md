# Name

make-metric-report -- generate consolidated runtime analysis metric report

# Synopsis

	usage: make-metric-report [-h] [--srcdir SRCDIR] [--reportdir REPORTDIR]
                               --proof PROOF [PROOF ...] [--verbose] [--debug]

# Description

This is a front end for the metric_reportt module that viewer uses to scan relevant
viewer metric json files for multiple proof harnesses and produce a consolidated
runtime analysis metric summary report. Output is a html file runtime_analysis_report.

Simple uses of make-coverage are

    # Generate all viewer metric data by running cbmc-viewer command
    make-metric-report --proof proof1 proof2 ... --srcdir /usr/project --reportdir html_report_dir

Type "make-metric-report --help" for a complete list of command line options.
