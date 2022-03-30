# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Version number."""

NAME = "CBMC viewer"
NUMBER = "2.12"
VERSION = "{} {}".format(NAME, NUMBER)

def version(display=False):
    """The version of cbmc viewer."""

    if display:
        print(VERSION)
    return VERSION
