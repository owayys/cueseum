from cues.grading import is_correct

from cueseum.parallel import timed_map

_tokenizer = None


def _init(tokenizer):
    global _tokenizer
    _tokenizer = tokenizer


def _score(item):
    gt, completion, style, budgets = item
    ids = _tokenizer.encode(completion, add_special_tokens=False)
    return [is_correct(gt, completion if len(ids) <= b else _tokenizer.decode(ids[:b]), style) for b in budgets]


def rescore(tokenizer, items, budgets, timeout=60, max_timeout_share=0.01):
    jobs = [(gt, completion, style, tuple(budgets)) for gt, completion, style in items]
    return timed_map(_score, jobs, lambda item: ["timeout"] * len(budgets), timeout, _init, (tokenizer,), max_timeout_share)
