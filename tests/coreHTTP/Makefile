# The FreeRTOS coreHTTP respository
REPO_DIR = coreHTTP
REPO_URL = https://github.com/FreeRTOS/coreHTTP.git

# Paths in the repository
PROOF_DIR = test/cbmc/proofs

# Proofs in the repository
PROOFS = \
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

# Omit slow proofs in the repository
#	HTTPClient_AddHeader \
#	HTTPClient_InitializeRequestHeaders \
#	HTTPClient_Send \

# Commits of cbmc-viewer to compare on coreHTTP
COMMIT1 ?= master
COMMIT2 ?= $$(git branch --show-current)

default: clone build compare

# Clone the repository and break the proofs
clone:
	$(RM) -r $(REPO_DIR)
	git clone $(REPO_URL) $(REPO_DIR)
	cd $(REPO_DIR); git submodule update --init --checkout --recursive
	cd $(REPO_DIR); git apply $(abspath bug.patch)

# Run the proofs and build the reports (using any version of viewer)
#   EXTERNAL_SAT_SOLVER= to ensure cbmc uses minisat and not kissat
build:
	cd $(REPO_DIR)/$(PROOF_DIR); \
	    EXTERNAL_SAT_SOLVER= \
	    run-cbmc-proofs.py --proofs $(PROOFS)

# Run the two commits of cbmc-viewer on the coreHTTP proofs and
# compare the results
compare:
	../bin/difference.py --verbose --force \
		--viewer $(abspath ../..) \
		--commits $(COMMIT1) $(COMMIT2) \
		--proofs $(abspath coreHTTP/test/cbmc/proofs)

clean:
	$(RM) *~
	$(RM) -r $(REPO_DIR)
