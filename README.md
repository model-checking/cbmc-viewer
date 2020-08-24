## AWS viewer for CBMC

The AWS viewer for CBMC (aka cbmc-viewer) scans the output of CBMC and
produces a browsable summary of the results in the form of a
collection of html pages.

For more information, see cbmc-viewer

* [cbmc-viewer](cbmc_viewer/doc/cbmc-viewer.md)

and the supporting tools (command-line front-ends for python modules used
to implement cbmc-viewer):

* [make-coverage](cbmc_viewer/doc/make-coverage.md)
* [make-loop](cbmc_viewer/doc/make-loop.md)
* [make-property](cbmc_viewer/doc/make-property.md)
* [make-reachable](cbmc_viewer/doc/make-reachable.md)
* [make-result](cbmc_viewer/doc/make-result.md)
* [make-source](cbmc_viewer/doc/make-source.md)
* [make-symbol](cbmc_viewer/doc/make-symbol.md)
* [make-trace](cbmc_viewer/doc/make-trace.md)

For all commands, the --help option prints detailed documentation of the
command line arguments.

## Installation

* Install python3:
    * On MacOS: brew install python3
    * On Ubuntu: sudo apt-get install python3
    * On Windows: download an installer from [www.python.org/downloads](https://www.python.org/downloads/)
* Install Exuberant Ctags:
    * On MacOS: brew install ctags
    * On Ubuntu: sudo apt-get install ctags
    * On Windows: download a zip file from [ctags.sourceforge.net](http://ctags.sourceforge.net/)
* Install cbmc-viewer as an ordinary Python pip package:
    * sudo make install

Developers of cbmc-viewer:
This package can be installed in "development mode."
In development mode, the scripts deployed by this package are available
via PATH, but the modules themselves can be edited directly in-place in this
repository.  Install with

* sudo make develop
* export PATH=$(pwd):$PATH

and uninstall with

* sudo make undevelop

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.
