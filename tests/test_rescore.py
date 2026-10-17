from cueseum import rescore


class CharTokenizer:
    def encode(self, text, add_special_tokens=False):
        return [ord(c) for c in text]

    def decode(self, ids):
        return "".join(map(chr, ids))


def test_rescore_truncates_and_grades():
    items = [("5", r" So \boxed{5}.", "boxed"), ("5", r" So \boxed{4}.", "boxed"), ("5", " none", "boxed")]
    out = rescore.rescore(CharTokenizer(), items, [4, 100])
    assert out == [[None, True], [None, False], [None, None]]
