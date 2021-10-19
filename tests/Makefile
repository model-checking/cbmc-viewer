SCRIPTS = \
  build-viewer-reports \
  compare-result \
  compare-source \
  compare-viewer-reports

pylint:
	pylint	\
		--disable=duplicate-code \
		--module-rgx '[\w-]+' \
	$(SCRIPTS)
