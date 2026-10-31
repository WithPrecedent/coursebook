"""Allows `coursebook` to be run with 'python -m coursebook'."""

from __future__ import annotations

from .cli import main

raise SystemExit(main())
