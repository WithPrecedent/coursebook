"""Tests for project files and settings."""

from __future__ import annotations

import pathlib

import pytest

from coursebook import settings
from tests.conftest import PROJECTS


def _write(folder: pathlib.Path, name: str, text: str) -> pathlib.Path:
    """Writes a project file and returns its path."""
    path = folder / name
    path.write_text(text, encoding = 'utf-8')
    return path


def test_read_ini() -> None:
    """Tests the `ini` project file of the coursebook test project."""
    project_settings, project_outline = settings.read_project_file(
        PROJECTS / 'coursebook' / 'project.ini')
    assert project_settings.name == 'Crazy Idea'
    assert project_settings.style == 'coursebook'
    assert project_settings.include == ['text', 'slides', 'notes']
    assert project_settings.slides_template == 'chalkboard'
    assert project_settings.author == ['Corey Rayburn Yung']
    assert len(project_outline) == 8


def test_read_toml() -> None:
    """Tests the `toml` project file of the law review test project."""
    project_settings, project_outline = settings.read_project_file(
        PROJECTS / 'law_review' / 'project.toml')
    assert project_settings.style == 'law review'
    assert project_settings.include == ['text', 'slides']
    assert project_settings.bibliography == ['references.bib']
    assert [entry.label for entry in project_outline] == [
        'I', 'II', 'A', 'B', 'III', 'A', 'B', 'IV']


def test_ini_repeated_labels(tmp_path: pathlib.Path) -> None:
    """Tests that an `ini` outline may repeat labels."""
    path = _write(tmp_path, 'project.ini', (
        '[project]\nname = Test\n\n[OUTLINE]\n# A comment\nI: One\nA: Sub\n'
        'II: Two\nA: Sub Two\n'))
    _, project_outline = settings.read_project_file(path)
    assert [entry.title for entry in project_outline] == [
        'One', 'Sub', 'Two', 'Sub Two']


def test_ini_types(tmp_path: pathlib.Path) -> None:
    """Tests converting `ini` values."""
    path = _write(tmp_path, 'project.ini', (
        '[Project]\nName: Test\nAuthors: King, Jr.; Doe\nTOC: no\n'
        'Number Headings: yes\nInclude: Slides,manuscript\n'
        'Course Number: 101\n\n[Outline]\nI: One\n'))
    project_settings, _ = settings.read_project_file(path)
    assert project_settings.author == ['King, Jr.', 'Doe']
    assert project_settings.table_of_contents is False
    assert project_settings.number_headings is True
    assert project_settings.include == ['slides', 'text']
    assert project_settings.extras == {'course_number': 101}


def test_formats(tmp_path: pathlib.Path) -> None:
    """Tests settings with more than one format."""
    path = _write(tmp_path, 'project.ini', (
        '[Project]\nText Format: word, PDF\nNotes Formats: html\n\n'
        '[Outline]\nI: One\n'))
    project_settings, _ = settings.read_project_file(path)
    assert project_settings.formats_for('text') == ['word', 'PDF']
    assert project_settings.formats_for('notes') == ['html']
    assert project_settings.formats_for('slides') == ['powerpoint']


def test_yaml(tmp_path: pathlib.Path) -> None:
    """Tests a `yaml` project file with mapping and string outline items."""
    path = _write(tmp_path, 'project.yaml', (
        'project:\n  name: Test\n  author: Doe\n'
        'outline:\n  - I: One\n  - "A: Sub"\n  - 1: Deep\n'))
    project_settings, project_outline = settings.read_project_file(path)
    assert project_settings.author == ['Doe']
    assert [entry.level for entry in project_outline] == [0, 1, 2]


def test_outline_inside_project_table(tmp_path: pathlib.Path) -> None:
    """Tests a `toml` outline inside the project table."""
    path = _write(tmp_path, 'project.toml', (
        '[project]\nname = "Test"\noutline = [["I", "One"], "II: Two", '
        '["III", "Three", "three_notes.md"]]\n'))
    project_settings, project_outline = settings.read_project_file(path)
    assert 'outline' not in project_settings.extras
    assert len(project_outline) == 3
    assert project_outline.entries[2].file == 'three_notes.md'


@pytest.mark.parametrize(('name', 'text', 'match'), [
    ('project.ini', '[Outline]\nI: One\n', 'no \\[Project\\]'),
    ('project.ini', 'Name: x\n', 'not a valid ini'),
    ('project.toml', 'outline = []\n', 'no "project" table'),
    ('project.toml', '[project\n', 'could not be read'),
    ('project.toml', '[project]\noutline = "I: x"\n', 'must be a list'),
    ('project.yaml', 'project: {}\noutline: [[1, 2, 3, 4]]\n', 'label and'),
    ('project.ini', '[Project]\nInclude: handouts\n', 'unknown section'),
    ('project.ini', '[Project]\nTOC: maybe\n', 'yes or no')])
def test_invalid_project_files(
        tmp_path: pathlib.Path,
        name: str,
        text: str,
        match: str) -> None:
    """Tests project files that are not valid."""
    path = _write(tmp_path, name, text)
    with pytest.raises(ValueError, match = match):
        settings.read_project_file(path)


def test_unsupported_extension(tmp_path: pathlib.Path) -> None:
    """Tests a project file with an unsupported extension."""
    path = _write(tmp_path, 'project.json', '{}')
    with pytest.raises(ValueError, match = 'not an ini'):
        settings.read_project_file(path)


def test_find_project_file(tmp_path: pathlib.Path) -> None:
    """Tests finding the project file, ignoring case."""
    path = _write(tmp_path, 'Project.INI', '')
    assert settings.find_project_file(tmp_path) == path
    _write(tmp_path, 'project.toml', '')
    with pytest.raises(ValueError, match = 'more than one'):
        settings.find_project_file(tmp_path)


def test_find_project_file_missing(tmp_path: pathlib.Path) -> None:
    """Tests a folder without a project file and a missing folder."""
    with pytest.raises(FileNotFoundError, match = 'no project file'):
        settings.find_project_file(tmp_path)
    with pytest.raises(FileNotFoundError, match = 'does not exist'):
        settings.find_project_file(tmp_path / 'missing')
    with pytest.raises(FileNotFoundError, match = 'not found'):
        settings.read_project_file(tmp_path / 'project.ini')


def test_settings_helpers() -> None:
    """Tests the format and template helpers."""
    project_settings = settings.Settings(text_template = 'house')
    assert project_settings.formats_for('slides') == ['powerpoint']
    assert project_settings.template_for('notes') == 'house'
    assert project_settings.template_for('slides') is None
