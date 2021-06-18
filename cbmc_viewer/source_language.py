# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Source file language for language dependent features."""

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
    def get_default_language(cls):
        return cls._default_language

    @classmethod
    def get_default_language_or_fail(cls):
        if cls._default_language == None:
            raise Exception("Default language is not set.")
        
        return cls._default_language
    
    @classmethod
    def set_default_language(cls, lang):
        assert lang in cls.ALL_LANGUAGE_NAMES, f"Invalid language: {lang}"
        
        cls._default_language = cls.get_language(lang)

    ######################################
    # Utility functions

    @staticmethod
    def get_language(name):
        'Gets the language utility class from a string name.'
        name_map = {
            Language.C: C,
            Language.RUST: Rust
        }
        return name_map[name]

    @staticmethod
    def get_language_name(lang):
        'Gets the string name of a language from the utility class.'
        return lang.get_name()

    ######################################
    # Language specific utility functions
    # These should be over-ridden by 
    # specific language implementations

    @classmethod
    def get_name(cls):
        """The name of the language"""
        return cls.get_default_language_or_fail().get_name()

    @classmethod
    def get_pretty_name_regex(cls):
        """A regex pattern to match pretty names,
        and which group in the pattern should be used"""
        return cls.get_default_language_or_fail().get_pretty_name_regex()

    @classmethod
    def get_symbol_regex(cls):
        """A regex pattern to match symbol names,
        and which group in the pattern should be used"""
        return cls.get_default_language_or_fail().get_symbol_regex()


class C(Language):
    """C-specific utility functions."""

    @staticmethod
    def get_name():
        return Language.C

    @staticmethod
    def get_pretty_name_regex():
        return '.*[^\S]([a-zA-Z0-9_]+)$', 1

    @staticmethod
    def get_symbol_regex():
        return '^(tag-)?([a-zA-Z0-9_]+)$', 2

class Rust(Language):
    """Rust-specific utility functions."""

    @staticmethod
    def get_name():
        return Language.RUST

    @staticmethod
    def get_pretty_name_regex():
        return '^([a-zA-Z0-9_<>: ]+)$', 1

    @staticmethod
    def get_symbol_regex():
        return '^([a-zA-Z0-9_]+)$', 1
