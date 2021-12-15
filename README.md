## AWS viewer for CBMC

[CBMC Viewer](https://github.com/awslabs/aws-viewer-for-cbmc) scans
the output of CBMC and produces a summary that can be opened in any
web browser to understand and debug CBMC findings.
[CBMC](https://github.com/diffblue/cbmc) is a "C Bounded Model
Checker" that has been widely-used to demonstrate the correctness of
critical C code.

This package provides a set of command-line tools that scan the
verification artifacts produced by CBMC to answer interesting
questions like "What are the results of the property checking?"
(`make-result`) and "What are the results of the coverage checking?"
(`make-coverage`) and "What are the error traces discovered?"
(`make-trace`). The answer to each question is given in the form of a
json blob that summarizes the answer.

This package provides a command line tool `cbmc-viewer` that renders
the answers to these questions into a set of web pages that can be
opened in a web browser and studied to understand and debug CBMC findings.  By
default, `cbmc-viewer` runs the various `make-*` tools itsef before
rendering the results.  Other tools can use the `make-*` tools to do
other analysis.  For example, a different tool could combine the results
of all proofs in a project into a single project summary, or could render the
results within a integrated development environment.

For more information, see cbmc-viewer

* [cbmc-viewer](cbmc_viewer/doc/cbmc-viewer.md)

and the supporting command-line tools

* [make-coverage](cbmc_viewer/doc/make-coverage.md)
* [make-loop](cbmc_viewer/doc/make-loop.md)
* [make-property](cbmc_viewer/doc/make-property.md)
* [make-reachable](cbmc_viewer/doc/make-reachable.md)
* [make-result](cbmc_viewer/doc/make-result.md)
* [make-source](cbmc_viewer/doc/make-source.md)
* [make-symbol](cbmc_viewer/doc/make-symbol.md)
* [make-trace](cbmc_viewer/doc/make-trace.md)

For all commands, the --help option prints detailed documentation of
the command line arguments, and the --verbose and --debug options may
help figure out what is going on when something unexpected happens.

## Installation

General users should follow the installation instructions on the
[release page](https://github.com/awslabs/aws-viewer-for-cbmc/releases/latest).

Developers should install the package in "development mode:"

* Follow the instructions on the
  [release page](https://github.com/awslabs/aws-viewer-for-cbmc/releases/latest)
  to install the dependencies.
* Clone the repository with `git clone https://github.com/awslabs/aws-viewer-for-cbmc.git cbmc-viewer`
* To install development mode, in the directory `cbmc-viewer`,
  run `make develop` followed by `export PATH=$(pwd):$PATH`.
* To uninstall development mode, in the directory `cbmc-viewer`,
  run `make undevelop`.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.
