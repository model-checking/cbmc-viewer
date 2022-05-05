SCRIPTS = \
  build-viewer-reports \
  compare-result \
  compare-source \
  compare-trace \
  compare-viewer-reports

PYLINT=pylint

pylint:
	$(PYLINT) \
		--disable=missing-function-docstring \
		--disable=too-many-arguments \
		\
		--disable=duplicate-code \
		--module-rgx '[\w-]+' \
	$(SCRIPTS) *.py
