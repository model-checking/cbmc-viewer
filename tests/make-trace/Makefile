SHELL=bash

MAKE_TRACE = make-trace
COMPARE_TRACES = ./compare-traces

TRACE_ROOT= /Users/mrtuttle/cbmc/scripts/cbmc-viewer/make/test/freertos
TRACE_GOTO= $(TRACE_ROOT)/tools/cbmc/proofs/HTTP/IotHttpsClient_AddHeader

default: trace

trace: traces-txt.json traces-json.json traces-xml.json
	diff {.,output}/traces-txt.json
	diff {.,output}/traces-json.json
	diff {.,output}/traces-xml.json
	$(COMPARE_TRACES) traces-txt.json traces-json.json traces-xml.json

traces-txt.json: input/result.txt
	$(MAKE_TRACE) --srcdir $(TRACE_ROOT) --wkdir $(TRACE_GOTO) $< > $@

traces-json.json: input/result.json
	$(MAKE_TRACE) --srcdir $(TRACE_ROOT)  $< > $@

traces-xml.json: input/result.xml
	$(MAKE_TRACE) --srcdir $(TRACE_ROOT)  $< > $@

clean:
	$(RM) *~
	$(RM) traces-txt.json traces-json.json traces-xml.json

.PHONY: trace clean
