"""Main file for unit tests."""

from __future__ import annotations

import coursebook


def test_coursebook() -> None:
    assert coursebook.__version__ == '0.1.0'

if __name__ == '__main__':
    test_coursebook()
