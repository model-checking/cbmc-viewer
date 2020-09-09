#!/usr/bin/env python3

"""Package set up script for cbmc-viewer."""

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="cbmc-viewer",
    version="2.0",
    author="Mark R. Tuttle",
    author_email="mrtuttle@amazon.com",
    description="A CBMC viewer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/awslabs/aws-viewer-for-cbmc",
    packages=setuptools.find_packages(),
    license="Apache License 2.0",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
    install_requires=[
        "jinja2",
        "setuptools",
        "voluptuous",
    ],
    include_package_data=True,
    package_data={
        "cbmc_viewer": [
            "doc/*",
            "templates/*",
            "viewer.css",
            "viewer.js"
        ]
    },
    entry_points={
        "console_scripts": [
            "cbmc-viewer = cbmc_viewer.viewer:viewer",
            "make-coverage = cbmc_viewer.make_coverage:main",
            "make-loop = cbmc_viewer.make_loop:main",
            "make-property = cbmc_viewer.make_property:main",
            "make-reachable = cbmc_viewer.make_reachable:main",
            "make-result = cbmc_viewer.make_result:main",
            "make-source = cbmc_viewer.make_source:main",
            "make-symbol = cbmc_viewer.make_symbol:main",
            "make-trace = cbmc_viewer.make_trace:main",
            "make-alias = cbmc_viewer.make_alias:main"
        ]
    }
)
