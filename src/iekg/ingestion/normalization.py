"""Label normalization for linking mentions to nodes.

The matching rules of the thesis (section 5.2.5.4): lower case, no accents, no
punctuation, collapsed spaces, and grammatical number reduced to the singular.
The test cases' evaluator applies the same rules, so linking and evaluation
agree on when two labels name the same thing.
"""

import re
import unicodedata


def normalize_label(label: str) -> str:
    text = unicodedata.normalize("NFD", label.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[\W_]", " ", text)
    # The singular, crudely: a final "s" goes from every word. Both sides of a
    # comparison lose it, so "bases" meets "base" and "redes" meets "rede".
    return " ".join(word.removesuffix("s") for word in text.split() if word.removesuffix("s"))
