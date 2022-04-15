# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""CBMC properties checked during property checking.

The Result module describes the results of CBMC property checking, the
Coverage module describes the results of CBMC coverage checking, and
the Property module describes the properties checked during property
checking.
"""

import json
import logging

import voluptuous
import voluptuous.humanize

from cbmc_viewer import filet
from cbmc_viewer import parse
from cbmc_viewer import srcloct
from cbmc_viewer import util

JSON_TAG = "viewer-property"

################################################################
# Property validator

VALID_PROPERTY_DEFINITION = voluptuous.Schema({
    'class': str,       # eg, "pointer dereference"
    'description': str, # eg, "pointer outside dynamic object"
    'expression': str,
    'location': srcloct.VALID_SRCLOC
}, required=True)

VALID_PROPERTY = voluptuous.Schema({
    'properties': {
        # property name -> property definition
        voluptuous.Optional(str): VALID_PROPERTY_DEFINITION
    }
}, required=True)

################################################################

def key(name):
    """A key for sorting property names like function.property.index"""

    try:
        dot = name.rindex('.')
        return (name[:dot].lower(), int(name[dot+1:]))
    except ValueError:
        logging.warning("Property name not of the form STRING.INTEGER: %s",
                        name)
        return (name, 0)

################################################################

class Property:
    """CBMC properties checked during property checking."""

    def __init__(self, property_lists=None):
        """Load CBMC properties from lists of properties."""

        property_lists = property_lists or []

        def handle_duplicates(name, defn1, defn2):
            logging.warning("Found duplicate property definition: "
                            "%s: %s %s <- %s %s",
                            name,
                            defn1["location"]["file"],
                            defn1["location"]["line"],
                            defn2["location"]["file"],
                            defn2["location"]["line"])

        self.properties = util.merge_dicts(property_lists, handle_duplicates)
        self.validate()

    def __repr__(self):
        """A dict representation of an property table."""

        self.validate()
        return self.__dict__

    def __str__(self):
        """A string representation of an property table."""

        return json.dumps({JSON_TAG: self.__repr__()}, indent=2, sort_keys=True)

    def validate(self):
        """Validate properties."""

        return voluptuous.humanize.validate_with_humanized_errors(
            self.__dict__, VALID_PROPERTY
        )

    def dump(self, filename=None, directory=None):
        """Write properties to a file or stdout."""

        util.dump(self, filename, directory)

    def names(self):
        """Names of known properties."""

        return self.properties.keys()

    def lookup(self, name):
        """Look up all known information for named property."""

        return self.properties.get(name)

    def get_description(self, name):
        """Get description of named property."""

        return (self.lookup(name) or {}).get('description') or name

    def get_srcloc(self, name):
        """Get source location of named property."""

        return (self.lookup(name) or {}).get('location')

################################################################

class PropertyFromJson(Property):
    """Load property table from the output of make-property.

    Given a list of json files containing property definitions
    produced by make-property, merge these lists into a single list
    of properties.
    """

    def __init__(self, json_files):

        super().__init__(
            [parse.parse_json_file(json_file)[JSON_TAG]["properties"]
             for json_file in json_files]
        )

################################################################

class PropertyFromCbmcJson(Property):
    """Load properties from output of 'cbmc --show-properties --json-ui'."""

    def __init__(self, json_files, root):

        super().__init__(
            [load_cbmc_json(json_file, root) for json_file in json_files]
        )

def load_cbmc_json(jsonfile, root):
    """Load a json file produced by cbmc --show-properties --json-ui."""

    json_data = parse.parse_json_file(jsonfile)
    assert json_data is not None

    # Search cbmc output for {"properties": [ PROPERTY ]}
    asserts = [json_map for json_map in json_data if "properties" in json_map]
    if len(asserts) != 1:
        raise UserWarning("Expected 1 set of properties in cbmc output, "
                          "found {}".
                          format(len(asserts)))

    # Each PROPERTY a loop property and definition
    root = srcloct.abspath(root)
    return {
        property['name']: {
            'class': property['class'],
            'description': property['description'],
            'expression': property['expression'],
            'location': srcloct.json_srcloc(property['sourceLocation'], root)
        }
        for property in asserts[0]["properties"]
    }

################################################################

class PropertyFromCbmcXml(Property):
    """Load properties from output of 'cbmc --show-properties --xml-ui'."""

    def __init__(self, xml_files, root):

        super().__init__(
            [load_cbmc_xml(xml_file, root) for xml_file in xml_files]
        )

def load_cbmc_xml(xmlfile, root):
    """Load a json file produced by cbmc --show-properties --xml-ui."""

    xml_data = parse.parse_xml_file(xmlfile)
    assert xml_data is not None

    root = srcloct.abspath(root)
    return {
        property.get("name"): {
            "class": property.get("class"),
            "description": property.find("description").text,
            "expression": property.find("expression").text,
            'location': srcloct.xml_srcloc(property.find("location"), root)
        }
        for property in xml_data.iter("property")
    }

################################################################
# make-property

# pylint: disable=inconsistent-return-statements

def fail(msg):
    """Log failure and raise exception."""

    logging.info(msg)
    raise UserWarning(msg)

def make_property(args):
    """The implementation of make-property."""

    viewer_property, cbmc_property, srcdir = args.viewer_property, args.cbmc_property, args.srcdir

    if viewer_property:
        if filet.all_json_files(viewer_property):
            return PropertyFromJson(viewer_property)
        fail("Expected json files: {}".format(viewer_property))

    if cbmc_property and srcdir:
        if filet.all_json_files(cbmc_property):
            return PropertyFromCbmcJson(cbmc_property, srcdir)
        if filet.all_xml_files(cbmc_property):
            return PropertyFromCbmcXml(cbmc_property, srcdir)
        fail("Expected json files or xml files, not both: {}"
             .format(cbmc_property))

    logging.info("make-property: nothing to do: need "
                 "cbmc property listing results (cbmc --show-properties) and --srcdir or "
                 "--viewer-property")
    return Property()

################################################################
