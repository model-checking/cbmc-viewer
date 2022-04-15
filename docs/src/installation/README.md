# Installation


## Brew installation

On MacOS, we recommend installing with [brew](https://brew.sh/).
Install with
```
  brew tap aws/tap
  brew install cbmc-viewer universal-ctags
```
and upgrade to the latest version with
```
  brew upgrade cbmc-viewer
```

The [brew home page](https://brew.sh/) gives instructions for installing brew.
The command `brew tap aws/tap` taps the AWS repository that contains the
brew package.
Installing `ctags` is optional, [see below](#installation-notes).

## Pip installation

On all machines, you can install with [pip](https://pypi.org/project/pip/).
Install with
```
  python3 -m pip install cbmc-viewer
  brew install universal-ctags
```
or
```
  python3 -m pip install cbmc-viewer
  apt install universal-ctags
```
and upgrade to the latest version with
```
  python3 -m pip install --upgrade cbmc-viewer
```

The [python download page](https://www.python.org/downloads/)
gives instructions for installing python and pip.
Installing `ctags` is optional, [see below](#installation-notes).

## Developers

Developers can install the package in "editable mode" which makes
it possible to modify the code in the source tree and then run the command
from the command line as usual to test the changes.
First, optionally install ctags as described above.  Then

* Clone the repository with
  ```
  git clone https://github.com/model-checking/cbmc-viewer cbmc-viewer
  ```
* Install into a virtual environment with
  ```
  cd cbmc-viewer
  make develop
  ```
  At this point you can either activate the virtual environment with
  ```
  source /tmp/cbmc-viewer/bin/activate
  ```
  or simply add the virtual environment to your path with
  ```
  export PATH=$PATH:/tmp/cbmc-viewer/bin
  ```

* Uninstall with
  ```
  cd cbmc-viewer
  make undevelop
  ```

## Installation notes

If you have difficulty installing these tools, please let us know by
submitting a [GitHub issue](https://github.com/model-checking/cbmc-viewer/issues).

The installation of `ctags` is optional, but without ctags, `cbmc-viewer`
will fail to link some symbols appearing in error traces to their
definitions in the source code. The ctags tool has a long history. The
[original ctags](https://en.wikipedia.org/wiki/Ctags) was resplaced by
[exhuberant ctags](http://ctags.sourceforge.net/) which was replaced by
[universal ctags](https://github.com/universal-ctags/ctags).
They all claim to be backwards compatible.
We recommend universal ctags.
