# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Source file language for language dependent features."""

import re

class Language:
    """A utility class to handle language-specific functionality.

    The class acts as the main API for language-specific functionality.
    It:
    - Provides language constants and utility functions
    - Acts as a super-class to all specfic language classes
    - Provides language-specific utility functions and automatically
      redirects to the correct language utility class
    """

    ######################################
    # Constants

    C = "C"
    RUST = "rust"
    ALL_LANGUAGE_NAMES = [C, RUST]

    ######################################
    # Default language handlers

    _default_language = None

    @classmethod
    def default_language(cls, lang=None):
        'Getter and setter for default source language.'
        if lang:
            assert lang in cls.ALL_LANGUAGE_NAMES, f"Invalid language: {lang}"
            cls._default_language = cls.get_language(lang)
            return cls._default_language

        assert cls._default_language is not None, "Default language is not set."
        return cls._default_language

    ######################################
    # Utility functions

    @staticmethod
    def get_language(name):
        'Gets the language utility class from a string name.'
        name_map = {
            Language.C: CLanguage,
            Language.RUST: RustLanguage
        }
        return name_map[name]

    @staticmethod
    def get_language_name(lang):
        'Gets the string name of a language from the utility class.'
        return lang.name()

    ######################################
    # Language specific utility functions
    # These should be over-ridden by
    # specific language implementations

    @classmethod
    def name(cls):
        """The name of the language"""
        return cls.default_language().name()

    @classmethod
    def match_pretty_name(cls, name):
        """Match and return a pretty name, or return None"""
        return cls.default_language().match_pretty_name(name)

    @classmethod
    def match_symbol(cls, name):
        """Match and return a symbol name, or return None"""
        return cls.default_language().match_symbol(name)


class CLanguage(Language):
    """C-specific utility functions."""

    @staticmethod
    def name():
        return Language.C

    @staticmethod
    def match_pretty_name(name):
        last = name.split(" ")[-1]
        if re.match('^[a-zA-Z0-9_]+$', last):
            return last
        return None

    @staticmethod
    def match_symbol(name):
        last = name.split(" ")[-1]
        match = re.match('^(tag-)?([a-zA-Z0-9_]+)$', last)
        if match:
            return match.group(2)
        return None

class RustLanguage(Language):
    """Rust-specific utility functions."""

    @staticmethod
    def name():
        return Language.RUST

    @staticmethod
    def match_pretty_name(name):
        if re.match('^[a-zA-Z0-9_<>: ]+$', name):
            return name
        return None

    @staticmethod
    def match_symbol(name):
        if re.match('^[a-zA-Z0-9_]+$', name):
            return name
        return None
