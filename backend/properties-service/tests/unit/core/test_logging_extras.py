"""Guards against a class of bug that only shows up at runtime.

`logging.makeRecord` raises KeyError if `extra=` carries a key that collides with
a reserved LogRecord attribute, so a single bad log call takes down the endpoint
that makes it — and only when that line is actually reached.
"""
import ast
import logging
import pathlib

import pytest

SRC = pathlib.Path(__file__).resolve().parents[3] / "src"

RESERVED = set(
    logging.LogRecord("", 0, "", 0, "", None, None).__dict__
) | {"message", "asctime", "taskName"}


def _extra_keys():
    """Yields (file, lineno, key) for every literal key passed to `extra=`."""
    for path in SRC.rglob("*.py"):
        if "__pycache__" in str(path):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and node.keywords):
                continue
            for kw in node.keywords:
                if kw.arg != "extra" or not isinstance(kw.value, ast.Dict):
                    continue
                for key in kw.value.keys:
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        yield path.relative_to(SRC), node.lineno, key.value


def test_no_log_extra_collides_with_a_reserved_logrecord_attribute():
    clashes = [
        f"{path}:{lineno} -> {key!r}"
        for path, lineno, key in _extra_keys()
        if key in RESERVED
    ]
    assert not clashes, "log extras collide with reserved LogRecord attributes: " + ", ".join(clashes)


def test_the_guard_actually_catches_a_known_reserved_name():
    """Fails if RESERVED stops covering the names that bit us in practice."""
    assert {"filename", "lineno", "module", "name", "args"} <= RESERVED


@pytest.mark.parametrize("bad_key", ["filename", "lineno", "module"])
def test_logging_rejects_reserved_keys(bad_key):
    """Documents the failure mode the guard exists to prevent."""
    with pytest.raises(KeyError):
        logging.getLogger("probe").makeRecord(
            "probe", logging.INFO, "f", 1, "msg", None, None, extra={bad_key: "x"}
        )
