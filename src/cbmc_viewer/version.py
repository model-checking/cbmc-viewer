# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Version number."""

NAME = "CBMC viewer"
NUMBER = "3.11.1"
VERSION = f"{NAME} {NUMBER}"

def version(display=False):
    """The version of cbmc viewer."""

    if display:
        print(VERSION)
    return VERSION
