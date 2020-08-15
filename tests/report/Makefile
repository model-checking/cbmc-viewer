FREERTOS = ../freertos
ADDHEADER = tools/cbmc/proofs/HTTP/IotHttpsClient_AddHeader

VIEWER = cbmc-viewer
MAKE_SOURCE = make-source

PATCH = $(abspath bug.patch)

default: report

source.json:
	$(MAKE_SOURCE) --srcdir $(FREERTOS) --wkdir $(FREERTOS)/$(ADDHEADER) > $@

report: source.json
#	$(MAKE) unpatch patch
	$(VIEWER) \
	  --viewer-source $< \
	  --goto IotHttpsClient_AddHeader.goto \
	  --srcdir $(FREERTOS) \
	  --reportdir report\
	  --result result.xml \
	  --property property.xml \
	  --coverage coverage.xml  $(ARGS)

patch:
	cd $(FREERTOS)/tools/cbmc/proofs && ./prepare.py
	cd $(FREERTOS); patch -p1 < $(PATCH)

unpatch:
	cd $(FREERTOS) && git clean -fdx && git checkout .
	cd $(FREERTOS)/freertos_kernel && git clean -fdx && git checkout .

clean: unpatch
	$(RM) *~ \#*
	$(RM) *.json
	$(RM) TAGS-*
	$(RM) -r html report report-old report-new

.PHONY: report patch unpatch clean
