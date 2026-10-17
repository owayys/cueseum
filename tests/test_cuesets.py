from cueseum import cuesets


class GreedyTokenizer:
    vocab = ["ab", "a", "b", "c"]

    def encode(self, text, add_special_tokens=False):
        ids = []
        while text:
            i = next(i for i, v in enumerate(self.vocab) if text.startswith(v))
            ids.append(i)
            text = text[len(self.vocab[i]):]
        return ids


def test_token_report():
    r = cuesets.token_report(GreedyTokenizer(), "a", {"merge": "b", "clean": "c"})
    assert r["merge"] == {"cue": "b", "ids": [0], "merges": True}
    assert r["clean"] == {"cue": "c", "ids": [3], "merges": False}


def test_roundtrip(tmp_path):
    cues = {"okay": " Okay,", "nl": " \n\nOkay"}
    cuesets.save(tmp_path / "c.json", cues)
    assert cuesets.load(tmp_path / "c.json") == cues
