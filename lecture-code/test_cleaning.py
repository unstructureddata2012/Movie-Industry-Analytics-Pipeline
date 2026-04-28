import pandas as pd
import numpy as np
import re

def clean_author(name):
    # Strip whitespace and collapse internal spaces.
    if pd.isna(name):
        return name
    return re.sub(r"\s+", " ", name.strip())

def clean_language(lang):
    # Lowercase and fill missing.
    if pd.isna(lang):
        return "und"
    return lang.strip().lower()


class TestCleanAuthor:
    def test_strips_whitespace(self):
        assert clean_author("  Alice  ") == "Alice"

    def test_collapses_internal_spaces(self):
        assert clean_author("Bob   Smith") == "Bob Smith"

    def test_handles_none(self):
        assert pd.isna(clean_author(None))

    def test_handles_nan(self):
        assert pd.isna(clean_author(float("nan")))

    def test_normal_name_unchanged(self):
        assert clean_author("Élise Müller") == "Élise Müller"


class TestCleanLanguage:
    def test_lowercase(self):
        assert clean_language("EN") == "en"

    def test_fills_none(self):
        assert clean_language(None) == "und"

    def test_strips_and_lowers(self):
        assert clean_language("  BS ") == "bs"
