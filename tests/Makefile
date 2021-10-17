SCRIPTS = \
  build-viewer-reports \
  compare-result \
  compare-source \
  compare-viewer-reports

default:
	@ echo Nothing to do for $@

pylint:
	pylint	\
		--disable=duplicate-code \
		--module-rgx '[\w-]+' \
	$(SCRIPTS)
