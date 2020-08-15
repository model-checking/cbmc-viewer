SHELL=bash

MAKE_COVERAGE = make-coverage

FREERTOS = /Users/mrtuttle/cbmc/scripts/cbmc-viewer/test/freertos

default: coverage

coverage: coverage-json.json coverage-xml.json coverage-json2.json coverage-xml2.json coverage-load.json
	diff coverage-json.json output/coverage-json.json
	diff coverage-xml.json output/coverage-xml.json
	diff coverage-json.json coverage-xml.json
	diff coverage-json.json coverage-json2.json
	diff coverage-xml.json coverage-xml2.json
	diff coverage-json.json coverage-load.json

coverage-json.json: input/coverage.json
	$(MAKE_COVERAGE) --srcdir $(FREERTOS) $<  > $@

coverage-json2.json: input/coverage.json
	$(MAKE_COVERAGE) --srcdir $(FREERTOS) $<  $< > $@

coverage-xml.json: input/coverage.xml
	$(MAKE_COVERAGE) --srcdir $(FREERTOS) $< > $@

coverage-xml2.json: input/coverage.xml
	$(MAKE_COVERAGE) --srcdir $(FREERTOS) $< $< > $@

coverage-load.json: coverage-json.json
	$(MAKE_COVERAGE) --srcdir $(FREERTOS) --viewer-coverage $< $< > $@


clean:
	$(RM) *~
	$(RM) coverage-json.json coverage-xml.json coverage-json2.json coverage-xml2.json coverage-load.json

.PHONY: coverage clean
