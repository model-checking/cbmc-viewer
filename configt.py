# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""CBMC viewer configuration."""

import parse

EXPECTED_MISSING = 'expected-missing-functions'

class Config:
    """Manage CBMC viewer configuration settings."""

    def __init__(self, config_file=None):
        self.file = config_file
        self.missing_functions = []

        if config_file is None:
            return

        config_data = parse.parse_json_file(config_file)
        if config_data:
            self.missing_functions = config_data.get(EXPECTED_MISSING, [])

    def expected_missing_functions(self):
        """Return list of expected missing functions."""

        return self.missing_functions
