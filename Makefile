# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

default:
	@echo Nothing to make

pylint:
	pylint	\
		--disable=fixme \
		--disable=duplicate-code \
		--disable=too-many-arguments \
		--disable=too-few-public-methods \
		--disable=too-many-branches \
		--module-rgx '[\w-]+' \
	*.py \
	make-property \
	make-coverage \
	make-loop \
	make-reachable \
	make-result \
	make-source \
	make-symbol \
	make-trace \
	cbmc-viewer

clean:
	$(RM) *~
	$(RM) *.pyc
	$(RM) -r __pycache__
