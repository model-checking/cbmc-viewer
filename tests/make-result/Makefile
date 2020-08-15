SHELL=bash

MAKE_RESULT = make-result
COMPARE_RESULT = ./compare-result

default: result

result: result-txt.json result-json.json result-xml.json result-json2.json
	diff {.,output}/result-txt.json
	diff {.,output}/result-json.json
	diff {.,output}/result-xml.json

	$(COMPARE_RESULT) result-txt.json result-json.json result-xml.json

	cat result-txt.json | jq '.["result"]' > /tmp/txt.json
	cat result-json.json | jq '.["result"]' > /tmp/json.json
	cat result-xml.json | jq '.["result"]' > /tmp/xml.json
	cat result-json2.json | jq '.["result"]' > /tmp/json2.json
	diff /tmp/xml.json /tmp/json.json
	diff /tmp/xml.json /tmp/txt.json
	diff /tmp/xml.json /tmp/json2.json

result-txt.json: input/result.txt
	$(MAKE_RESULT)  $< > $@

result-json.json: input/result.json
	$(MAKE_RESULT) $< > $@

result-xml.json: input/result.xml
	$(MAKE_RESULT)  $< > $@

result-json2.json: result-json.json
	$(MAKE_RESULT) --viewer-result $< $< > $@

clean:
	$(RM) *~
	$(RM) result-txt.json result-json.json result-xml.json result-json2.json

.PHONY: result clean
