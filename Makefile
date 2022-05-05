# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# See https://packaging.python.org/en/latest/tutorials/installing-packages/
# See https://packaging.python.org/tutorials/packaging-projects/
# python3 -m ensurepip
# python3 -m pip install --upgrade pip setuptools wheel
# python3 -m pip install --upgrade build
# python3 -m pip install --upgrade pylint

default:
	@echo Nothing to make

################################################################
# Run pylint over the package

PYLINT=pylint

pylint: pylint-viewer pylint-tests

pylint-viewer:
	$(PYLINT) \
		--disable=duplicate-code \
		--disable=fixme \
		--disable=invalid-repr-returned \
		--disable=too-few-public-methods \
		--disable=too-many-arguments \
		--disable=too-many-branches \
		--module-rgx '[\w-]+' \
	    src/cbmc_viewer/*.py

pylint-tests:
	$(MAKE) -C tests/bin PYLINT=$(PYLINT) pylint

################################################################
# Build the distribution package

build:
	python3 -m build

unbuild:
	$(RM) -r dist

################################################################
# Install the package into a virtual environment in development mode
#
# Note: Editable installs from pyproject.toml require at least pip 21.3

VENV = /tmp/cbmc-viewer
develop:
	python3 -m venv $(VENV)
	$(VENV)/bin/python3 -m pip install --upgrade pip
	$(VENV)/bin/python3 -m pip install -e .
	@ echo
	@ echo "Package installed into virtual environment at $(VENV)."
	@ echo "Activate virtual environment with 'source $(VENV)/bin/activate'"
	@ echo "(or add it to PATH with 'export PATH=\$$PATH:$(VENV)/bin')."
	@ echo

undevelop:
	$(RM) -r $(VENV)

################################################################
# Install the package
#
# Note: This requires write permission (sudo): It updates the system
# site-packages directory.


install:
	python3 -m pip install --verbose .

uninstall:
	python3 -m pip uninstall --verbose --yes cbmc-viewer

################################################################
# Clean up after packaging and installation

clean:
	$(RM) *~
	$(RM) *.pyc
	$(RM) -r __pycache__

veryclean: clean unbuild undevelop

################################################################

.PHONY: default pylint build unbuild develop undevelop install uninstall
.PHONY: clean veryclean
