# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""The known file types."""

import enum
import os

################################################################

class File(enum.Enum):
    """The known file types."""

    TEXT = 1
    XML = 2
    JSON = 3

def filetype(filename):
    """Return the file type denoted by the filename extension."""

    if filename is None:
        return None

    if not isinstance(filename, str):
        raise UserWarning("Filename is not a string: {}".format(filename))

    # The filename extension: expected to be one of txt, jsn, json, or xml
    file_extension = os.path.splitext(filename)[1].lower().lstrip('.')

    # Return the file type
    try:
        return {
            'log': File.TEXT,
            'txt': File.TEXT,
            'jsn': File.JSON,
            'json': File.JSON,
            'xml': File.XML
        }[file_extension]
    except KeyError:
        raise UserWarning(
            "Can't determine file type of file {}".format(filename)
        ) from None # squash the KeyError context, raise just a UserWarning

################################################################

def is_text_file(txt):
    """File is a text file."""
    return filetype(txt) == File.TEXT
def is_json_file(json):
    """File is a json file."""
    return filetype(json) == File.JSON
def is_xml_file(xml):
    """File is an xml file."""
    return filetype(xml) == File.XML

def all_text_files(txts):
    """Files are text files."""
    return all(is_text_file(txt) for txt in txts)
def all_json_files(jsons):
    """Files are json files."""
    return all(is_json_file(json) for json in jsons)
def all_xml_files(xmls):
    """Files are xml files."""
    return all(is_xml_file(xml) for xml in xmls)

def any_text_files(txts):
    """Any of the files are text files."""
    return any(is_text_file(txt) for txt in txts)

################################################################
