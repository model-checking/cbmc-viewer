# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Miscellaneous functions."""

import logging
import os

################################################################

def flatten(groups):
    """Flatten a list of lists to a single list"""

    return [item
            for group in groups if group is not None
            for item in group if item is not None]

def choose(items):
    """Choose an item from a list (use a deterministic choice)"""

    items = sorted({item for item in items if item is not None})
    if len(items) != 1:
        logging.debug("No unique element in %s", items)
    return items[0] if items else None

################################################################

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

################################################################

def dump(data, filename=None, directory='.'):
    """Write data to a file or stdout."""

    # directory defaults to '.' even if dump is called with directory=None
    directory = directory or '.'

    if filename:
        path = os.path.normpath(os.path.join(directory, filename))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as fileobj:
            print(data, file=fileobj)
    else:
        print(data)

def save(obj, path=None):
    """Save an object to a file or to stdout"""

    if path is None:
        print(obj)
        return

    with open(path, 'w', encoding='utf-8') as output:
        print(obj, file=output)
    return

################################################################
