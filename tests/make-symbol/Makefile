SHELL=bash

MAKE_SYMBOL = make-symbol
MAKE_SOURCE = make-source

ENTRY=IotHttpsClient_AddHeader
FREERTOS = ../freertos
ADD_HEADER = tools/cbmc/proofs/HTTP/$(ENTRY)

default: symbol

symbol: symbols-build.json symbols-find.json symbols-walk.json
	diff {.,output}/symbols-build.json
#	diff {.,output}/symbols-goto.json
	diff symbols-find.json symbols-walk.json
# Definitions in submodules are too changable.
#	diff {.,output}/symbols-find.json
#	diff {.,output}/symbols-walk.json

# Requires a --blddir flag to work
#symbols-goto.json: input/IotHttpsClient_AddHeader.goto
#	$(MAKE_SYMBOL) --srcdir $(FREERTOS) --wkdir $(FREERTOS)/$(ADD_HEADER) --goto $< > $@

symbols-build.json: sources-build.json
	$(MAKE_SYMBOL) --srcdir $(FREERTOS) --viewer-source sources-build.json > $@

symbols-find.json: sources-find.json
	$(MAKE_SYMBOL) --srcdir $(FREERTOS) --viewer-source sources-find.json --verbose > $@

symbols-walk.json: sources-walk.json
	$(MAKE_SYMBOL) --srcdir $(FREERTOS) --viewer-source sources-walk.json --verbose > $@

sources-build.json: $(FREERTOS)
	$(MAKE_SOURCE) --srcdir $< --wkdir $</$(ADD_HEADER) > $@

sources-find.json: $(FREERTOS)
	$(MAKE_SOURCE) --srcdir $< --source-method find > $@

sources-walk.json: $(FREERTOS)
	$(MAKE_SOURCE) --srcdir $< --source-method walk > $@


clean:
	$(RM) *~
	$(RM) symbols-build.json symbols-goto.json symbols-find.json symbols-walk.json
	$(RM) sources-build.json sources-find.json sources-walk.json

.PHONY: symbol clean
