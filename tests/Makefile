SHELL=bash

default:
	@echo "Nothing to do"

freertos:
	git clone \
		https://github.com/aws/amazon-freertos.git \
		freertos
	cd freertos; git checkout e984d9463b7cb594434f07e8435869bab8787ba0
	cd freertos; git submodule update --init
	cd freertos/tools/cbmc/proofs; python3 ./prepare.py
