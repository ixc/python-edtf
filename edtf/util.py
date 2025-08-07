#!/usr/bin/env python3

"""
Assorted utility functions.
"""

from functools import update_wrapper
from logging import warning
from traceback import extract_stack


def remapparams(**remap):
    """
    Remap the specified named parameters.

    Example to support an obsolete `parseAll` parameter:

        @remapparams(parseAll='parse_all')
        def parse(s, parse_all=True):

    """
    if not remap:
        raise ValueError("no parameters specified for remapping")
    for old, new in remap.items():
        if new in remap:
            raise ValueError(f"{old}={new!r}: {new!r} is also remapped")

    def remapparams_decorator(func):
        """The decorator to apply the remappings."""
        # a record of callers whose parameters were remapped
        remapped_callers = set()

        def remapparams_wrapper(*a, **kw):
            remappings = {}
            for param, value in list(kw.items()):
                try:
                    remapped = remap[param]
                except KeyError:
                    continue
                if remapped in kw:
                    raise ValueError(
                        f"remap {param}= to {remapped}=: this is already present in the keyword arguments"
                    )
                del kw[param]
                kw[remapped] = value
                remappings[param] = remapped
            if remappings:
                caller_frame = extract_stack(limit=2)[-2]
                caller_key = caller_frame.filename, caller_frame.lineno
                if caller_key not in remapped_callers:
                    warning(
                        "call of %s.%s() from %s:%d: remapped the following obsolete parameters: %s",
                        func.__module__,
                        func.__name__,
                        caller_frame.filename,
                        caller_frame.lineno,
                        ", ".join(
                            sorted(f"{old}->{new}" for old, new in remappings.items())
                        ),
                    )
                    remapped_callers.add(caller_key)
            return func(*a, **kw)

        update_wrapper(remapparams_wrapper, func)
        return remapparams_wrapper

    return remapparams_decorator


if __name__ == "__main__":

    @remapparams(parseAll="parse_all")
    def parser(s, parse_all=True):
        pass

    assert parser.__name__ == "parser"  # noqa: S101
    parser("foo")
    # this should not warn
    parser("foo", parse_all=False)
    # this should warn, but only once
    for _ in 1, 2:
        parser("foo", parseAll=False)
    try:
        parser("foo", parseAll=False, parse_all=True)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError because of duplicated parameters")

    try:

        @remapparams()
        def no_remappings():
            pass
    except ValueError:
        pass
    else:
        raise AssertionError(
            "expected ValueError from @remapparams() because no remappings"
        )
    try:

        @remapparams(p1="p2", p2="p3")
        def no_remappings():
            pass
    except ValueError:
        pass
    else:
        raise AssertionError(
            "expected ValueError from @remapparams() because p1 remaps to another remapped parameter"
        )
