# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Source file language for language dependent features."""

class Language:
    C = "C"
    RUST = "rust"
    ALL_LANGUAGE_NAMES = [C, RUST]

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

    @staticmethod
    def get_language(name):
        name_map = {
            Language.C: C,
            Language.RUST: Rust
        }
        return name_map[name]

    @staticmethod
    def get_language_name(lang):
        return lang.get_name()

    @classmethod
    def get_name(cls):
        return cls.get_default_language_or_fail().get_name()

    @classmethod
    def get_pretty_name_regex(cls):
        return cls.get_default_language_or_fail().get_pretty_name_regex()

    @classmethod
    def get_symbol_regex(cls):
        return cls.get_default_language_or_fail().get_symbol_regex()

Language.default_language = Language

class Rust(Language):
    @staticmethod
    def get_name():
        return Language.RUST

    @staticmethod
    def get_pretty_name_regex():
        return '^([a-zA-Z0-9_<>: ]+)$', 1

    @staticmethod
    def get_symbol_regex():
        return '^([a-zA-Z0-9_]+)$', 1

class C(Language):
    @staticmethod
    def get_name():
        return Language.C

    @staticmethod
    def get_pretty_name_regex():
        return '.*[^\S]([a-zA-Z0-9_]+)$', 1

    @staticmethod
    def get_symbol_regex():
        return '^(tag-)?([a-zA-Z0-9_]+)$', 2
