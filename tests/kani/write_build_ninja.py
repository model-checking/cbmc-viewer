#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import re
import subprocess
import sys

import ninja_syntax

RULE_NAME = 'kani'
BUILD_COUNT = 0

def rust_sources(root):
    sources = subprocess.run(
        ['find', root, '-name', '*.rs'],
        encoding='utf-8',
        universal_newlines=True,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    ).stdout.splitlines()
    # source files with names including 'ignore' and 'fixme' are broken
    # source file 'ForeignItems/main.rs' is also broken
    tags = ['ignore', 'fixme', 'tests/kani/ForeignItems/main.rs']
    return [src for src in sources if all(tag not in src for tag in tags)]

def kani_pragma(pragma, rust_code):
    # Examples of kani pragmas:
    # // kani-verify-fail
    # // kani-check-fail
    # // kani-flags: --default-unwind 8
    try:
        regexp = fr'//[ \t]*{pragma}([^\n]*)'
        return re.search(regexp, rust_code).group(1).strip()
    except AttributeError: # 'NoneType' object has no attribute 'group'
        return None

def kani_verify_fail(rust_code):
    return kani_pragma('kani-verify-fail', rust_code) is not None

def kani_check_fail(rust_code):
    return kani_pragma('kani-check-fail', rust_code) is not None

def kani_flags(rust_code):
    return kani_pragma('kani-flags:', rust_code) or ""

def ninja_build_statements(source):
    source = Path(source)
    with open(source, encoding='utf-8') as src:
        rust_code = src.read()
    if kani_verify_fail(rust_code) or kani_check_fail(rust_code):
        return []

    # Warning: concurrent invocations of kani in a single directory
    # should generate race conditions that have so far been
    # unobserved.  The count variable here is just a hack just to get
    # ninja to run.
    # TODO: Define one pool of depth 1 for each directory, and assign
    # all kani runs on all proofs in that directory to that pool.
    global BUILD_COUNT
    BUILD_COUNT += 1
    return [{'outputs': [f'{source}-{BUILD_COUNT}'],
             'rule': RULE_NAME,
             'inputs':  str(source),
             'variables': {'dir': str(source.parent),
                           'src': str(source.name),
                           'flags': kani_flags(rust_code)}}]

def build_ninja_file(sources, build='build.ninja'):
    with open(build, 'w', encoding='utf-8') as output:
        writer = ninja_syntax.Writer(output)
        writer.rule(RULE_NAME, 'cd "${dir}" && kani ${flags} --visualize ${src}')
        for source in sources:
            for build in ninja_build_statements(source):
                writer.build(**build)

def main():
    try:
        root = sys.argv[1]
    except IndexError:
        root = 'kani/tests/kani'
    sources = rust_sources(root)
    build_ninja_file(sources)

if __name__ == "__main__":
    main()
