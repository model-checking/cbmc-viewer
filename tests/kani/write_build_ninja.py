#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import re
import subprocess
import sys

import ninja_syntax

RULE_NAME = 'kani'

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
    return [Path(src) for src in sources if all(tag not in src for tag in tags)]

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

def pool_name(pool):
    return re.sub('[^a-zA-Z0-9_]', '_', str(pool))

def ninja_pools(sources):
    pools = {source.parent for source in sources}
    return [{'name': pool_name(pool), 'depth': 1} for pool in pools]

def ninja_rules(sources):
    dirs = {source.parent for source in sources}
    return [{'name': pool_name(dir),
             'command': f'cd "{dir}" && kani ${{flags}} --visualize ${{src}}',
             'pool': pool_name(dir)} for dir in dirs]

def ninja_builds(source):
    with open(source, encoding='utf-8') as src:
        rust_code = src.read()
    if kani_verify_fail(rust_code) or kani_check_fail(rust_code):
        return []

    return [{'outputs': [f'build-{source}'],
             'rule': pool_name(source.parent),
             'inputs':  str(source),
             'variables': {'src': str(source.name),
                           'flags': kani_flags(rust_code)}}]

def build_ninja_file(sources, build_ninja='build.ninja'):
    with open(build_ninja, 'w', encoding='utf-8') as output:
        writer = ninja_syntax.Writer(output)
        for pool in ninja_pools(sources):
            writer.pool(**pool)
        for rule in ninja_rules(sources):
            writer.rule(**rule)
        for source in sources:
            for build in ninja_builds(source):
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
