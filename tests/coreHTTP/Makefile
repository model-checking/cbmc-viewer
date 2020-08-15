# This regression test for cbmc-viewer builds the proofs in the
# FreeRTOS coreHTTP repository and compares the results to expected
# results.  It does a diff of the html trees produced; and it does a
# diff of the json files produced, except that the viewer-result.json
# and viewer-source.json can include embedded runtimes and path names
# that can differ and must by handled by comparison scripts.

COMPARE_RESULT = ../compare-result
COMPARE_SOURCE = ../compare-source

# The FreeRTOS coreHTTP respository
REPO_NAME = coreHTTP
REPO_URL = https://github.com/FreeRTOS/coreHTTP.git
REPO_COMMIT = 9f511d57f4f4048654389259a1a483b0f71f6951

# Path to the directory inside the repository containing the proofs
REPO_PROOF = test/cbmc/proofs

# Path to the html and json output inside the directory for a particular proof
REPO_HTML = html/html
REPO_JSON = html/json

# Path to the directory containing the expected results of the proofs
EXPECTED_RESULT = expected

REPO_PROOF_DIR = $(REPO_NAME)/$(REPO_PROOF)
EXPECTED_PROOF_DIR = $(EXPECTED_RESULT)

PROOFS = \
	HTTPClient_AddHeader \
	HTTPClient_AddRangeHeader \
	HTTPClient_ReadHeader \
	HTTPClient_strerror \
	findHeaderFieldParserCallback \
	findHeaderOnHeaderCompleteCallback \
	findHeaderValueParserCallback \
	httpParserOnBodyCallback \
	httpParserOnHeaderFieldCallback \
	httpParserOnHeaderValueCallback \
	httpParserOnHeadersCompleteCallback \
	httpParserOnMessageBeginCallback \
	httpParserOnMessageCompleteCallback \
	httpParserOnStatusCallback

# omit slow proofs
#	HTTPClient_InitializeRequestHeaders \
#	HTTPClient_Send \


JSON = \
	viewer-coverage.json \
	viewer-loop.json \
	viewer-property.json \
	viewer-reachable.json \
	viewer-symbol.json \
	viewer-trace.json

RESULT_JSON = viewer-result.json
SOURCE_JSON = viewer-source.json

default: clean clone build compare-html compare-json

clone:
	git clone $(REPO_URL) $(REPO_NAME)
	cd $(REPO_NAME); git checkout -b cbmc-viewer-regression-testing $(REPO_COMMIT)
	cd $(REPO_NAME); git submodule update --init --checkout --recursive
	cd $(REPO_NAME); git apply ../bug.patch
	cd $(REPO_NAME); git apply ../run-cbmc-proofs.patch

build:
	cd $(REPO_PROOF_DIR); python3 run-cbmc-proofs.py --proofs $(PROOFS)

compare-html:
	for proof in $(PROOFS); do \
	  echo $$proof; \
	  diff -q -r $(EXPECTED_PROOF_DIR)/$$proof/$(REPO_HTML) $(REPO_PROOF_DIR)/$$proof/$(REPO_HTML); \
	done

compare-json:
	for proof in $(PROOFS); do \
	  echo $$proof; \
	  echo $(RESULT_JSON); \
	  $(COMPARE_RESULT) \
	    $(EXPECTED_PROOF_DIR)/$$proof/$(REPO_JSON)/$(RESULT_JSON) \
	    $(REPO_PROOF_DIR)/$$proof/$(REPO_JSON)/$(RESULT_JSON); \
	  echo $(SOURCE_JSON); \
	  $(COMPARE_SOURCE) \
	    $(EXPECTED_PROOF_DIR)/$$proof/$(REPO_JSON)/$(SOURCE_JSON) \
	    $(REPO_PROOF_DIR)/$$proof/$(REPO_JSON)/$(SOURCE_JSON); \
	  for json in $(JSON); do \
	    echo $$json; \
	    diff -q \
	      $(EXPECTED_PROOF_DIR)/$$proof/$(REPO_JSON)/$$json \
	      $(REPO_PROOF_DIR)/$$proof/$(REPO_JSON)/$$json; \
	  done; \
	done;

clean:
	$(RM) -r $(REPO_NAME)
	$(RM) *~
