# The FreeRTOS coreHTTP respository
REPO_DIR = coreHTTP
REPO_URL = https://github.com/FreeRTOS/coreHTTP.git

# Paths in the repository
PROOF_DIR = test/cbmc/proofs

# Proofs in the repository
PROOF = HTTPClient_AddRangeHeader

UNIVERSAL=$$(ctags --version | grep Universal)
EXUBERANT=$$(ctags --version | grep Exuberant)

default: clone build compare

# Clone the repository
clone:
	$(RM) -r $(REPO_DIR)
	git clone $(REPO_URL) $(REPO_DIR)
	cd $(REPO_DIR); git submodule update --init --checkout --recursive

# Run a proofs
#   EXTERNAL_SAT_SOLVER= to ensure cbmc uses minisat and not kissat
build:
	cd $(REPO_DIR)/$(PROOF_DIR)/$(PROOF); \
	    EXTERNAL_SAT_SOLVER= \
	    make goto

symbol:
	cbmc-viewer symbol \
		--goto $(REPO_DIR)/$(PROOF_DIR)/$(PROOF)/gotos/$(PROOF)_harness.goto \
		--srcdir $(REPO_DIR) > symbol.json

legacy: symbol
	diff symbol.json symbol-legacy.json

exuberant: symbol
	diff symbol.json symbol-exuberant.json

universal: symbol
	diff symbol.json symbol-universal.json

clean:
	$(RM) *~ symbol.json

veryclean: clean
	$(RM) -r $(REPO_DIR)
