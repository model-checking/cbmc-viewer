# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

default:
	@echo Nothing to make

SCRIPTS = \
	cbmc-viewer \
	make-coverage \
	make-loop \
	make-property \
	make-reachable \
	make-result \
	make-source \
	make-symbol \
	make-trace \

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
	*.py cbmc_viewer/*.py

################################################################

pip:
	./setup.py sdist bdist_wheel

unpip:
	./setup.py clean --all
	$(RM) -r dist cbmc_viewer.egg-info

################################################################

develop:
	./setup.py develop --script-dir .

undevelop:
	./setup.py develop --script-dir . --uninstall
	$(RM) $(SCRIPTS) easy_install easy_install-3.8
	$(RM) -r cbmc_viewer.egg-info

################################################################

test:
	tox

################################################################

install: pip
	cd .. && sudo python3 -m pip install $(abspath dist/cbmc_viewer-2.0-py3-none-any.whl)

uninstall:
	cd .. && sudo python3 -m pip uninstall -y cbmc-viewer


################################################################

clean:
	$(RM) *~
	$(RM) *.pyc
	$(RM) -r __pycache__


veryclean: clean undevelop unpip

################################################################

.PHONY: default pylint pip unpip develop undevelop clean veryclean
