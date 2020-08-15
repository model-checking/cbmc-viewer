SHELL=bash

MAKE_SOURCE = make-source
COMPARE_SOURCES = ./compare-sources

ENTRY=IotHttpsClient_AddHeader
FREERTOS = ../freertos
ADD_HEADER = tools/cbmc/proofs/HTTP/$(ENTRY)

default: source

source: sources-build.json sources-find.json sources-walk.json sources-merge.json
#	diff {.,output}/sources-goto.json
	diff sources-find.json sources-walk.json
	diff sources-find.json sources-merge.json
	python3 $(COMPARE_SOURCES) sources-build.json sources-find.json sources-walk.json

#	diff {.,output}/sources-build.json
#	diff {.,output}/sources-find.json
#	diff {.,output}/sources-walk.json

# Requires a --blddir flag to work
#sources-goto.json: input/IotHttpsClient_AddHeader.goto
#	$(MAKE_SOURCE) --srcdir $(FREERTOS) --wkdir /Users/mrtuttle/cbmc/scripts/cbmc-viewer/test/freertos/$(ADD_HEADER) --goto $< > $@

sources-build.json: $(FREERTOS)
	$(MAKE_SOURCE) --srcdir $< --wkdir $</$(ADD_HEADER) > $@

sources-find.json: $(FREERTOS)
	$(MAKE_SOURCE) --srcdir $< --source-method find > $@

sources-walk.json: $(FREERTOS)
	$(MAKE_SOURCE) --srcdir $< --source-method walk > $@

sources-find2.json: sources-find.json
	grep -v demos sources-find.json > $@

sources-merge.json: sources-find.json sources-find2.json
	$(MAKE_SOURCE) --srcdir $(FREERTOS) --viewer-source sources-find.json sources-find2.json > $@

clean:
	$(RM) *~
	$(RM) sources-build.json sources-find.json sources-walk.json
	$(RM) sources-merge.json sources-goto.json

.PHONY: source clean
