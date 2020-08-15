SHELL=bash

MAKE_PROPERTY = make-property

FREERTOS = /Users/mrtuttle/cbmc/scripts/cbmc-viewer/test/freertos

default: property

property: property-json.json property-xml.json
	diff property-json.json property-xml.json
	diff {.,output}/property-json.json
	diff {.,output}/property-xml.json

property-json.json: input/property.json
	$(MAKE_PROPERTY) --srcdir $(FREERTOS)  $< > $@

property-xml.json: input/property.xml
	$(MAKE_PROPERTY) --srcdir $(FREERTOS)  $< > $@

clean:
	$(RM) *~
	$(RM) property-json.json property-xml.json

.PHONY: property clean
