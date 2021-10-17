# Use the FreeRTOS coreHTTP proofs to compare two versions of cbmc-viewer.
#
# 1. make clone: Clone the repository and "break" the proofs
# 2. make build: Run the proofs and build the reports
# 3. Rebuild reports with viewer1
#    a. Ensure the command 'cbmc-viewer' runs viewer1
#    b. make reports1: Build the reports with viewer1
# 4. Rebuild reports with viewer2
#    a. Ensure the command 'cbmc-viewer' runs viewer2
#    b. make reports2: Build the reports with viewer2
# 5. make compare: Compare the results of viewer1 and viewer2

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

# Comparison scripts
BUILD_REPORTS = $(abspath ../build-viewer-reports)
COMPARE_REPORTS = $(abspath ../compare-viewer-reports)

REPORTS1 = $(abspath reports1)
REPORTS2 = $(abspath reports2)

default:
	@ echo Run
	@ echo "  make clone"
	@ echo "  make build"
	@ echo "  make reports1   # Ensure cbmc-viewer runs viewer1"
	@ echo "  make reports2   # Ensure cbmc-viewer runs viewer2"
	@ echo "  make compare"

# Clone the repository and break the proofs
clone:
	$(RM) -r $(REPO_DIR)
	git clone $(REPO_URL) $(REPO_DIR)
	cd $(REPO_DIR); git submodule update --init --checkout --recursive
	cd $(REPO_DIR); git apply $(abspath bug.patch)
	cd $(REPO_DIR)/$(TEMPLATE_DIR); git apply $(abspath run-cbmc-proofs.patch)

# Run the proofs and build the reports (using any version of viewer)
#   EXTERNAL_SAT_SOLVER= to ensure cbmc uses minisat and not kissat
#   TERM=vt100 so ninja knows what screen formatting characters to use
build:
	cd $(REPO_DIR)/$(PROOF_DIR); \
	    EXTERNAL_SAT_SOLVER= \
	    TERM=vt100 \
	    python3 run-cbmc-proofs.py --proofs $(PROOFS)


# Rebuild reports with viewer1 (with cbmc-viewer running viewer1)
reports1:
	cd $(REPO_DIR)/$(PROOF_DIR); $(BUILD_REPORTS) $(FLAGS) $(REPORTS1)

# Rebuild reports with viewer2 (with cbmc-viewer running viewer2)
reports2:
	cd $(REPO_DIR)/$(PROOF_DIR); $(BUILD_REPORTS) $(FLAGS) $(REPORTS2)

# Compare the results of viewer1 and viewer2
compare:
	$(COMPARE_REPORTS) $(FLAGS) $(REPORTS1) $(REPORTS2)

clean:
	$(RM) *~
	$(RM) -r $(REPORTS1)
	$(RM) -r $(REPORTS2)

veryclean: clean
	$(RM) -r $(REPO_DIR)

.PHONY: default clone build reports1 reports2 compare clean veryclean
