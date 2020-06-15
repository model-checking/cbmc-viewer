# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Miscellaneous functions."""

def merge_dicts(dicts, handle_duplicate=None):
    """Merge a list of dictionaries.

    Invoke handle_duplicate(key, val1, val2) when two dicts maps the
    same key to different values val1 and val2, maybe logging the
    duplication.
    """

    if not dicts:
        return {}

    if len(dicts) == 1:
        return dicts[0]

    if handle_duplicate is None:
        return {key: val for dict_ in dicts for key, val in dict_.items()}

    result = {}
    for dict_ in dicts:
        for key, val in dict_.items():
            if key in result and val != result[key]:
                handle_duplicate(key, result[key], val)
                continue
            result[key] = val
    return result
