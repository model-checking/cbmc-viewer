SHELL=bash

MAKE_LOOP = make-loop

FREERTOS = /Users/mrtuttle/cbmc/scripts/cbmc-viewer/make/test/freertos

default: loop

loop: loop-goto.json loop-json.json loop-xml.json loop-goto2.json
	diff loop-goto.json loop-xml.json
	diff loop-goto.json loop-json.json
	diff loop-goto.json loop-goto2.json
	-diff {.,output}/loop-goto.json
	-diff {.,output}/loop-json.json
	-diff {.,output}/loop-xml.json

loop-goto.json: input/IotHttpsClient_AddHeader.goto
	$(MAKE_LOOP) --srcdir $(FREERTOS) --goto $< > $@

cbmc-loop.json: input/IotHttpsClient_AddHeader.goto
	cbmc --show-loops --json-ui $< > $@

loop-json.json: cbmc-loop.json
	$(MAKE_LOOP) --srcdir $(FREERTOS) $< > $@

cbmc-loop.xml: input/IotHttpsClient_AddHeader.goto
	cbmc --show-loops --xml-ui $< > $@

loop-xml.json: cbmc-loop.xml
	$(MAKE_LOOP) --srcdir $(FREERTOS) $< > $@

loop-goto2.json: loop-goto.json
	$(MAKE_LOOP) --srcdir $(FREERTOS) --viewer-loop $< $< > $@

clean:
	$(RM) *~
	$(RM) loop-goto.json loop-json.json loop-xml.json loop-goto2.json

.PHONY: loop clean
