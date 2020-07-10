## AWS viewer for CBMC

The AWS viewer for CBMC (aka cbmc-viewer) scans the output of CBMC and
produces a browsable summary of the results in the form of a
collection of html pages.

For more information, see cbmc-viewer

* [cbmc-viewer](cbmc-viewer.md)

and the supporting tools (command-line front-ends for python modules used
to implement cbmc-viewer):

* [make-coverage](make-coverage.md)
* [make-loop](make-loop.md)
* [make-property](make-property.md)
* [make-reachable](make-reachable.md)
* [make-result](make-result.md)
* [make-source](make-source.md)
* [make-symbol](make-symbol.md)
* [make-trace](make-trace.md)

For all commands, the --help option prints detailed documentation of the
command line arguments.

## Installation

This package requires python3:

* On MacOS: brew install python3
* On Ubuntu: sudo apt-get install python3
* On Windows: download an installer from [www.python.org/downloads](https://www.python.org/downloads/)

This package requires the jinja and voluptuous python packages:

* python3 -m pip install -r requirements.txt

This package works best with Exuberant Ctags installed (which is different from Emacs ctags often installed as both ctags and etags):

* On MacOS: brew install ctags
* On Ubuntu: sudo apt-get install ctags
* On Windows: download a zip file from [ctags.sourceforge.net](http://ctags.sourceforge.net/)

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.
