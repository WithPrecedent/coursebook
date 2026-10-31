"""Tests for creating new projects and templates."""

from __future__ import annotations

import dataclasses
import pathlib
import zipfile

import docx
import pptx
import pytest

import coursebook
from coursebook import scaffold, settings


def test_create_project(tmp_path: pathlib.Path) -> None:
    """Tests a new project with the default outline."""
    folder = tmp_path / 'torts_seminar'
    created = scaffold.create_project(folder)
    assert folder / 'project.ini' in created
    assert (folder / 'visuals').is_dir()
    project_settings, project_outline = settings.read_project_file(
        folder / 'project.ini')
    assert project_settings.name == 'Torts Seminar'
    assert project_settings.style == 'coursebook'
    assert len(project_outline) == 4
    assert (folder / 'introduction.md').read_text(encoding = 'utf-8') == (
        '<text>\n\n\n<slides>\n\n\n<notes>\n')
    assert coursebook.Project.from_folder(folder).missing == []


@pytest.mark.parametrize('file_format', scaffold.PROJECT_FILE_FORMATS)
def test_project_file_formats(tmp_path: pathlib.Path, file_format: str) -> None:
    """Tests that each project file format can be read back."""
    lines = ['-: Preface', 'I: One: A Start', 'A: "Quoted"', 'II: Two']
    scaffold.create_project(
        tmp_path, name = 'Crazy Idea', style = 'law review',
        outline_lines = lines, file_format = file_format)
    project_settings, project_outline = settings.read_project_file(
        tmp_path / f'project.{file_format}')
    assert project_settings.name == 'Crazy Idea'
    assert project_settings.style == 'law review'
    assert [(entry.label, entry.title) for entry in project_outline] == [
        ('', 'Preface'), ('I', 'One: A Start'), ('A', '"Quoted"'),
        ('II', 'Two')]
    # The law review style has no notes.
    assert '<notes>' not in (tmp_path / 'two.md').read_text(encoding = 'utf-8')


def test_shared_titles_get_own_files(tmp_path: pathlib.Path) -> None:
    """Tests that entries with the same title get their own files."""
    scaffold.create_project(tmp_path, outline_lines = [
        'I: One', 'A: Overview', 'II: Two', 'A: Overview',
        'III: Three | chapters/three.md'])
    project = coursebook.Project.from_folder(tmp_path)
    assert [entry.file_name for entry in project.outline] == [
        'one.md', 'overview.md', 'two.md', 'overview_2.md',
        'chapters/three.md']
    assert project.missing == []


def test_existing_files_are_kept(tmp_path: pathlib.Path) -> None:
    """Tests that existing source files are not overwritten."""
    (tmp_path / 'introduction.md').write_text('Mine', encoding = 'utf-8')
    created = scaffold.create_project(tmp_path)
    assert tmp_path / 'introduction.md' not in created
    assert (tmp_path / 'introduction.md').read_text(encoding = 'utf-8') == (
        'Mine')
    with pytest.raises(FileExistsError, match = 'already has a project file'):
        scaffold.create_project(tmp_path)


def test_invalid_new_projects(tmp_path: pathlib.Path) -> None:
    """Tests an unknown file format, style, and outline."""
    with pytest.raises(ValueError, match = 'unknown project file format'):
        scaffold.create_project(tmp_path, file_format = 'json')
    with pytest.raises(ValueError, match = 'unknown style'):
        scaffold.create_project(tmp_path, style = 'memo')
    with pytest.raises(ValueError, match = 'cannot place'):
        scaffold.create_project(tmp_path, outline_lines = ['B: Wrong'])
    assert not list(tmp_path.iterdir())


def test_write_templates(tmp_path: pathlib.Path) -> None:
    """Tests writing the Word and PowerPoint templates of styles."""
    word = scaffold.write_template('law review', tmp_path / 'lr.docx')
    assert docx.Document(str(word)).styles['Normal'].font.name == (
        'Times New Roman')
    deck = scaffold.write_template('coursebook', tmp_path / 'deck.pptx')
    presentation = pptx.Presentation(str(deck))
    names = {layout.name for layout in presentation.slide_layouts}
    assert 'Section Header' in names
    with pytest.raises(FileExistsError, match = 'already exists'):
        scaffold.write_template('coursebook', deck)
    with pytest.raises(ValueError, match = 'must end with'):
        scaffold.write_template('coursebook', tmp_path / 'deck.pdf')


def test_write_templates_without_names(tmp_path: pathlib.Path) -> None:
    """Tests a style without a PowerPoint template."""

    @dataclasses.dataclass
    class PlainLecture(coursebook.Coursebook):
        slides_template: str | None = None

    deck = scaffold.write_template('plain lecture', tmp_path / 'plain.pptx')
    with zipfile.ZipFile(deck) as package:
        theme = package.read('ppt/theme/theme1.xml').decode('utf-8')
    assert 'chalkboard' not in theme
