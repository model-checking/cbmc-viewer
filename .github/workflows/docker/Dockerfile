################################################################
# Build stage

FROM ubuntu:20.04 AS build

ENV VIEWER_SOURCE=/tmp/viewer-source
ENV VIEWER_STAGING=/tmp/viewer-staging
ENV VIEWER_INSTALL=/usr/local/cbmc-viewer

# build
COPY . ${VIEWER_SOURCE}

# stage
RUN \
  rm -rf ${VIEWER_SOURCE}/.git* && \
  rm -rf ${VIEWER_SOURCE}/__pycache__  && \
  rm -rf ${VIEWER_SOURCE}/test && \
  mkdir -p ${VIEWER_STAGING} && \
  cp -RP ${VIEWER_SOURCE}/* ${VIEWER_STAGING}

################################################################
# Runtime stage

FROM ubuntu:20.04

VOLUME ["/home"]

ENV VIEWER_SOURCE=/tmp/viewer-source
ENV VIEWER_STAGING=/tmp/viewer-staging
ENV VIEWER_INSTALL=/usr/local/cbmc-viewer

ENV PATH="/usr/local/bin:/usr/local/cbmc-viewer:${PATH}"
ENV PS1="VIEWER:\w "

RUN echo PS1=\"${PS1}\" >> /root/.bashrc

# runtime dependencies
RUN \
  apt update && apt install -y \
    ctags \
    python-is-python3 \
    python3 \
    python3-pip \
  && rm -rf /var/lib/apt/lists/*
RUN python3 -m pip install voluptuous jinja2

# install
COPY --from=build ${VIEWER_STAGING} ${VIEWER_STAGING}
RUN \
  mkdir -p ${VIEWER_INSTALL} && \
  cp -RP ${VIEWER_STAGING}/* ${VIEWER_INSTALL}
