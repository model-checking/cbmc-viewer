default:
	@echo Nothing to do

pylint:
	pylint \
		--disable missing-function-docstring \
		--disable missing-module-docstring \
		--disable duplicate-code \
		--module-rgx '[\w-]+' \
		--max-line-length 80 \
	*.py
