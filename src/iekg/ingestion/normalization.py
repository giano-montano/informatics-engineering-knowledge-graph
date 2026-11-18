"""Label normalization for linking mentions to nodes.

The matching rules of the thesis (section 5.2.5.4): lower case, no accents, no
punctuation, collapsed spaces, and grammatical number reduced to the singular.
The test cases' evaluator applies the same rules, so linking and evaluation
agree on when two labels name the same thing.

One exception to "no punctuation": a "+" or "#" right after a letter, with no
letter after it, is part of the name (C++, C#, F#, B+). Dropping it would
merge C++ and C# with C. Elsewhere, as in "HTML+CSS" or "3+4", it is still
punctuation.
"""

import re
import unicodedata

# Words the singular below would turn into another term or mangle: acronyms
# whose final "s" is a letter of the name, and words that end in "s" already in
# the singular. Chosen from computing knowledge, never from the test cases.
PROTECTED = frozenset({"https", "ips", "ids", "ftps", "smtps", "imaps", "ldaps", "pop3s", "bus"})

# Possessive, so "c++x" does not keep the first "+" alone.
_SEPARATOR = re.compile(r"(?P<kept>(?<=[^\W\d_])[+#]++(?![^\W\d_]))|[\W_]")


def _singular(word: str) -> str:
    # The Spanish plural, roughly: "-s" after a vowel, "-es" after a consonant,
    # and "-ces" for a final "z". The key need not be a word ("variabl"); it is
    # never shown. Known misses: "meses" and "paises" (stressed vowel + "s").
    if word in PROTECTED:
        return word
    word = word.removesuffix("s")
    if len(word) > 2 and word[-1] == "e" and word[-2] not in "aeiou":
        word = word[:-1]
    if word.endswith("z"):
        word = word[:-1] + "c"
    return word


def normalize_label(label: str) -> str:
    text = unicodedata.normalize("NFD", label.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = _SEPARATOR.sub(lambda match: match["kept"] or " ", text)
    return " ".join(word for word in map(_singular, text.split()) if word)
