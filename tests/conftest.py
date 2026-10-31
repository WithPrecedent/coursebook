"""Shared fixtures for the `coursebook` tests."""

from __future__ import annotations

import pathlib
import shutil

import pytest

PROJECTS: pathlib.Path = pathlib.Path(__file__).parent / 'projects'


@pytest.fixture
def coursebook_project(tmp_path: pathlib.Path) -> pathlib.Path:
    """Returns a copy of the coursebook test project in a temp folder."""
    return pathlib.Path(
        shutil.copytree(PROJECTS / 'coursebook', tmp_path / 'coursebook'))


@pytest.fixture
def law_review_project(tmp_path: pathlib.Path) -> pathlib.Path:
    """Returns a copy of the law review test project in a temp folder."""
    return pathlib.Path(
        shutil.copytree(PROJECTS / 'law_review', tmp_path / 'law_review'))
