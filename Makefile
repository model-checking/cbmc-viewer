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

pylint:
	pylint	\
		--disable=unspecified-encoding \
		--disable=consider-using-f-string \
		\
		--disable=duplicate-code \
		--disable=fixme \
		--disable=invalid-repr-returned \
		--disable=too-few-public-methods \
		--disable=too-many-arguments \
		--disable=too-many-branches \
		--module-rgx '[\w-]+' \
	    src/cbmc_viewer/*.py
	$(MAKE) -C tests pylint

################################################################
# Build the distribution package

build:
	python3 -m build

unbuild:
	$(RM) -r dist

################################################################
# Install the package into this directory in development mode
#
# Note: This may require directory write permission (sudo): It may try
# to update cbmc-viewer.egg-link and easy-install.pth in site-packages.
# The Homebrew pip continues to update the system site-packages even
# with the --user flag to pip install.

develop:
	python3 -m pip install --verbose --editable . --user \
		--install-option="--script-dir=."
	@ echo
	@ echo "Add cbmc-viewer to PATH with 'export PATH=$$(pwd):\$$PATH'"
	@ echo

undevelop:
	python3 -m pip uninstall --verbose --yes cbmc-viewer
	$(RM) cbmc-viewer
	$(RM) make-coverage
	$(RM) make-loop
	$(RM) make-property
	$(RM) make-reachable
	$(RM) make-result
	$(RM) make-source
	$(RM) make-symbol
	$(RM) make-trace
	$(RM) -r src/cbmc_viewer/__pycache__/
	$(RM) -r src/cbmc_viewer.egg-info
	@ echo
	@ echo "This may leave cbmc-viewer in the bash command cache."
	@ echo "Delete cbmc-viewer from the cache with 'hash -d cbmc-viewer'."
	@ echo

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
