# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

SHELL=/bin/bash

# Assume cbmc and cbmc-viewer are installed in PATH
#   skip ./kani/scripts/setup/ubuntu/install_cbmc.sh
#   skip ./kani/scripts/setup/install_viewer.sh 2.11

KANI?=kani

# ARCH is ubuntu or macos-10.15
ARCH?=ubuntu

clone:
	git clone https://github.com/model-checking/kani.git $(KANI)
	cd $(KANI) && git submodule update --init

# MacOS warning: If brew fails trying to install ctags over
# universal-ctags, then replace ctags with universal-ctags
# ./kani/scripts/setup/macos-10.15/install_deps.sh

build:
	PATH=$$HOME/.cargo/bin:$$PATH $(MAKE) build_

build_:
	./$(KANI)/scripts/setup/$(ARCH)/install_deps.sh
	./$(KANI)/scripts/setup/install_rustup.sh
	cd $(KANI) && cargo build --workspace

test:
	PATH=$$HOME/.cargo/bin:$$(pwd)/$(KANI)/scripts:$$PATH $(MAKE) version test_

test_:
	./write_build_ninja.py $(KANI)/tests/kani
	ninja

version:
	@ echo cbmc --version: $$(cbmc --version) >&2
	@ echo cbmc-viewer --version: $$(cbmc-viewer --version) >&2
	@ echo kani --version: $$(kani --version) >&2

clean:
	$(RM) -r *~ build.ninja .ninja_log __pycache__

veryclean: clean
	$(RM) -r $(KANI)
