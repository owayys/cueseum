import multiprocessing as mp


def timed_map(fn, items, fallback, timeout=10, initializer=None, initargs=(), max_timeout_share=0.01):
    out, stalled = [], 0
    while len(out) < len(items):
        pool = mp.get_context("fork").Pool(1, initializer, initargs)
        jobs = pool.imap(fn, items[len(out):])
        try:
            while len(out) < len(items):
                out.append(jobs.next(timeout))
        except mp.TimeoutError:
            out.append(fallback(items[len(out)]))
            stalled += 1
            if stalled > max(1, max_timeout_share * len(items)):
                raise RuntimeError(f"{stalled} of {len(items)} items timed out")
        finally:
            pool.terminate()
    return out
