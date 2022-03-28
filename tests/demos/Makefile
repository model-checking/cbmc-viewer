# The FreeRTOS coreHTTP respository
REPO_DIR = coreHTTP
REPO_URL = https://github.com/FreeRTOS/coreHTTP.git

# Paths in the repository
PROOF_DIR = test/cbmc/proofs
TEMPLATE_DIR = test/cbmc/aws-templates-for-cbmc-proofs

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

default:
	@ echo Nothing to do.

# Clone the repository and break the proofs
clone:
	$(RM) -r $(REPO_DIR)
	git clone $(REPO_URL) $(REPO_DIR)
	cd $(REPO_DIR); git submodule update --init --checkout --recursive
	cd $(REPO_DIR); git apply $(abspath bug.patch)

# Run the proofs and build the reports (using any version of viewer)
#   EXTERNAL_SAT_SOLVER= to ensure cbmc uses minisat and not kissat
#   TERM=vt100 so ninja knows what screen formatting characters to use
build:
	cd $(REPO_DIR)/$(PROOF_DIR); \
	    EXTERNAL_SAT_SOLVER= \
	    run-cbmc-proofs.py --proofs $(PROOFS)

COMMIT1 = master
COMMIT2 = master

demo:
	../bin/difference.py --verbose --force \
		--viewer ../.. \
		--commits $(COMMIT1) $(COMMIT2) \
		--proofs coreHTTP/test/cbmc/proofs \
		--litani coreHTTP/test/cbmc/litani/litani
