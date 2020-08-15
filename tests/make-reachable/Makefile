SHELL=bash

MAKE_REACHABLE = make-reachable

FREERTOS = /Users/mrtuttle/cbmc/scripts/cbmc-viewer/test/freertos

default: reachable

reachable: reachable-goto.json reachable-json.json reachable-goto2.json
	diff reachable-goto.json reachable-json.json
	diff reachable-goto.json reachable-goto2.json
	-diff {.,output}/reachable-goto.json
	-diff {.,output}/reachable-json.json

reachable-goto.json: input/IotHttpsClient_AddHeader.goto
	$(MAKE_REACHABLE) --srcdir $(FREERTOS) --goto $< > $@

cbmc-reachable.json: input/IotHttpsClient_AddHeader.goto
	goto-analyzer --reachable-functions --json - $< > $@

reachable-json.json: cbmc-reachable.json
	$(MAKE_REACHABLE) --srcdir $(FREERTOS) $< > $@

# This goto-analyzer produces text and not xml
cbmc-reachable.xml: input/IotHttpsClient_AddHeader.goto
	goto-analyzer --reachable-functions --xml - $< > $@

reachable-xml.json: cbmc-reachable.xml
	$(MAKE_REACHABLE) --srcdir $(FREERTOS) $< > $@

reachable-goto2.json: reachable-goto.json
	$(MAKE_REACHABLE) --srcdir $(FREERTOS) --viewer-reachable $< $< > $@

clean:
	$(RM) *~
	$(RM) cbmc-reachable.json
	$(RM) reachable-goto.json reachable-json.json reachable-goto2.json

.PHONY: reachable clean
