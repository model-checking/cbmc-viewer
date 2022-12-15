# This compares the symbol tables produced by two versions of
# cbmc-viewer using the currently installed version of ctags.  Given
# two branches A and B of the cbmc-viewer repository, the command
#
#    make COMMIT1=A COMMIT2=B
#
# will install viewer in branch A into a virtual environment and run
# viewer to generate the symbols of a coreHTTP goto binary, do the
# same for branch B, and run diff on the results.
#
# The command will fail (correctly) if the repository contains dirty
# copies of files tracked by the repository.
#
# There are three versions of ctags: legacy, exuberant, and universal.
# On MacOS:
#   legacy ctags: installed by default
#   exuberant ctags: installed by "brew install ctags"
#   universal ctags: installed by "brew install universal-ctags"

# The FreeRTOS coreHTTP respository
REPO_DIR = coreHTTP
REPO_URL = https://github.com/FreeRTOS/coreHTTP.git

# The path to the proofs directory in coreHTTP
PROOF_DIR = test/cbmc/proofs

# The path to a proof under the proofs directory in coreHTTP
PROOF = HTTPClient_AddRangeHeader

default: clone goto compare

# Clone the coreHTTP repository
clone:
	$(RM) -r $(REPO_DIR)
	git clone $(REPO_URL) $(REPO_DIR)
	cd $(REPO_DIR) && git submodule update --init --checkout --recursive

# Make the coreHTTP goto binary
goto:
	$(MAKE) -C $(REPO_DIR)/$(PROOF_DIR)/$(PROOF) goto

# Compare the symbol tables produced by the two versions of
# cbmc-viewer denoted by COMMIT1 and COMMIT2.  For each commit,
# install viewer and build the symbol table, and the run diff.
COMMIT1 = master
COMMIT2 = master
SYMBOLS1 = symbol1.json
SYMBOLS2 = symbol2.json
compare:
	$(MAKE) VENV=$(VENV) COMMIT=$(COMMIT1) viewer
	PATH="$(VENV)/bin:$(PATH)" $(MAKE) SYMBOLS=$(SYMBOLS1) symbols

	$(MAKE) VENV=$(VENV) COMMIT=$(COMMIT2) viewer
	PATH="$(VENV)/bin:$(PATH)" $(MAKE) SYMBOLS=$(SYMBOLS2) symbols

	diff $(SYMBOLS1) $(SYMBOLS2)

# Install the version of cbmc-viewer denoted by COMMIT into a virtual
# environment denoted by VENV.  Record the name of the current branch
# in BRANCH, checkout and install the commit, and restore the current
# branch.
#
# NOTE: In what follows, using a SHA to restore the original commit
# leaves the repository in a detached HEAD state, which may be
# annoying to developers, but GitHub workflows check out the commits
# by SHA and not by branch, so `git branch --show-current` returns an
# empty string.
COMMIT = master
VENV = /tmp/cbmc-viewer
viewer:
	$(RM) -r $(VENV)
	SHA=$$(git rev-parse HEAD) && \
	git checkout $(COMMIT) && \
	$(MAKE) -C ../../.. VENV=$(VENV) develop && \
	git checkout $$SHA

# Generate the symbol table with cbmc-viewer
SYMBOLS = symbol.json
symbols:
	cbmc-viewer symbol \
		--goto $(REPO_DIR)/$(PROOF_DIR)/$(PROOF)/gotos/$(PROOF)_harness.goto \
		--srcdir $(REPO_DIR) > $(SYMBOLS)

clean:
	$(RM) *~ $(SYMBOLS1) $(SYMBOLS2)

veryclean: clean
	$(RM) -r $(REPO_DIR) $(VENV)

.PHONY: default goto clone compare viewer symbols clean veryclean
