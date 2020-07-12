# Call this makefile from the root of the repository
# make -f $(DOCKERPATH)/Makefile build
# make -f $(DOCKERPATH)/Makefile push

ACCT ?= markrtuttle
REPO ?= viewer-binaries
VER ?= latest

ROOT ?= ../../..
DOCKERPATH ?= .github/workflows/docker
DOCKERFILE ?= Dockerfile

TAG1 ?= $(ACCT)/$(REPO):$(VER)
TAG2 ?= $(ACCT)/$(REPO):latest

default:
	@echo Nothing to do for default.

build:
	cd $(ROOT) \
	  && docker build --tag $(TAG1) --file $(DOCKERPATH)/$(DOCKERFILE) .
	docker tag $(TAG1) $(TAG2)

push:
	docker push $(TAG1)
	docker push $(TAG2)
