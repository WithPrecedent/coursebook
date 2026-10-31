"""Tests for building projects."""

from __future__ import annotations

import logging
import pathlib
import sys
import zipfile

import docx
import pptx
import pytest

import coursebook
from coursebook import cli


def _headings(path: pathlib.Path) -> list[tuple[str, str]]:
    """Returns the style and text of each heading in a Word file."""
    document = docx.Document(str(path))
    return [
        (paragraph.style.name, paragraph.text)
        for paragraph in document.paragraphs
        if paragraph.style.name.startswith('Heading')]


def _slides(path: pathlib.Path) -> list[tuple[str, str]]:
    """Returns the layout and title of each slide in a PowerPoint file."""
    presentation = pptx.Presentation(str(path))
    slides = []
    for slide in presentation.slides:
        title = slide.shapes.title
        slides.append((
            slide.slide_layout.name, title.text if title is not None else ''))
    return slides


def _part(path: pathlib.Path, name: str) -> str:
    """Returns the text of a part of an Office file."""
    with zipfile.ZipFile(path) as package:
        return package.read(name).decode('utf-8')


def test_project_from_folder(coursebook_project: pathlib.Path) -> None:
    """Tests loading the coursebook test project."""
    project = coursebook.Project.from_folder(coursebook_project)
    assert isinstance(project.style, coursebook.Coursebook)
    assert project.include == ['text', 'slides', 'notes']
    assert project.missing == []
    assert project.unused == []
    assert project.output_folder == coursebook_project / 'output'


def test_assemble_text(coursebook_project: pathlib.Path) -> None:
    """Tests the combined markdown of the text."""
    text = coursebook.Project.from_folder(coursebook_project).assemble('text')
    assert text.startswith('# Introduction\n\nThis coursebook')
    assert '## Why It Matters' in text
    assert '[^introduction-1]' in text
    assert '[^literature_review-1]' in text
    assert '### The Underlying Facts' in text
    assert '# This is code, not a slide' in text
    assert '#### ' not in text


def test_assemble_slides(coursebook_project: pathlib.Path) -> None:
    """Tests the combined markdown of the slides."""
    slides = coursebook.Project.from_folder(coursebook_project).assemble(
        'slides')
    assert slides.startswith('# Introduction\n\n## Welcome')
    assert '# Literature Review\n\n## Literature Review\n\n- Three' in slides
    assert '# Supporting Work' not in slides
    assert '# My Cool Idea\n\n# Interesting Premise 1' in slides


def test_assemble_notes(coursebook_project: pathlib.Path) -> None:
    """Tests that the notes skip empty entries and copy visuals."""
    notes = coursebook.Project.from_folder(coursebook_project).assemble(
        'notes')
    assert '![Enrollment by year](chart.png){width=50%}' in notes
    assert 'Literature Review' not in notes
    assert '# My Cool Idea' in notes


def test_assemble_unknown_section(coursebook_project: pathlib.Path) -> None:
    """Tests that an unknown section raises an error."""
    project = coursebook.Project.from_folder(coursebook_project)
    with pytest.raises(ValueError, match = 'unknown section'):
        project.assemble('handouts')


def test_build_coursebook(coursebook_project: pathlib.Path) -> None:
    """Tests building the text, slides, and notes of a coursebook."""
    paths = coursebook.build(coursebook_project)
    output = coursebook_project / 'output'
    assert paths == [
        output / 'crazy_idea.docx',
        output / 'crazy_idea_slides.pptx',
        output / 'crazy_idea_notes.docx']
    assert _headings(paths[0]) == [
        ('Heading 1', 'Introduction'),
        ('Heading 2', 'Why It Matters'),
        ('Heading 1', 'Literature Review'),
        ('Heading 1', 'My Cool Idea'),
        ('Heading 2', 'Interesting Premise 1'),
        ('Heading 3', 'The Underlying Facts'),
        ('Heading 3', 'Supporting Work'),
        ('Heading 2', 'Interesting Premise 2'),
        ('Heading 1', 'Conclusion')]
    text = docx.Document(str(paths[0]))
    assert text.styles['Normal'].font.name == 'Georgia'
    assert any(name.startswith('word/media/') for name in zipfile.ZipFile(
        paths[0]).namelist())
    footnotes = _part(paths[0], 'word/footnotes.xml')
    assert 'crazy only in the best sense' in footnotes
    assert 'collected in the appendix' in footnotes
    # The table of contents is a field that Word fills in.
    assert 'TOC \\o' in _part(paths[0], 'word/document.xml')


def test_build_slides(coursebook_project: pathlib.Path) -> None:
    """Tests the slide deck of a coursebook."""
    path = coursebook.build(coursebook_project, include = ['slides'])[0]
    slides = _slides(path)
    assert slides[0] == ('Title Slide', 'Crazy Idea')
    assert slides[1:4] == [
        ('Section Header', 'Introduction'),
        ('Title and Content', 'Welcome'),
        ('Title and Content', '')]
    assert ('Title and Content', 'Literature Review') in slides
    assert ('Title and Content', 'The Facts') in slides
    presentation = pptx.Presentation(str(path))
    last = presentation.slides[len(presentation.slides) - 1]
    assert last.notes_slide.notes_text_frame.text == 'Leave time for questions.'
    assert 'chalkboard' in _part(path, 'ppt/theme/theme1.xml')


def test_build_notes(coursebook_project: pathlib.Path) -> None:
    """Tests the notes of a coursebook."""
    path = coursebook.build(coursebook_project, include = ['notes'])[0]
    assert path.name == 'crazy_idea_notes.docx'
    assert [text for _, text in _headings(path)] == [
        'Introduction', 'My Cool Idea', 'Conclusion']
    document = docx.Document(str(path))
    paragraphs = [paragraph.text for paragraph in document.paragraphs]
    assert 'A Coursebook: Notes' in paragraphs


def test_build_law_review(
        law_review_project: pathlib.Path,
        caplog: pytest.LogCaptureFixture) -> None:
    """Tests a law review with repeated labels, footnotes, and citations."""
    with caplog.at_level(logging.WARNING):
        text, slides = coursebook.build(law_review_project)
    assert 'purpose.md' in caplog.text
    assert text.name == 'a_modest_proposal_for_statutory_interpretation.docx'
    assert _headings(text) == [
        ('Heading 1', 'I. Introduction'),
        ('Heading 1', 'II. Background'),
        ('Heading 2', 'A. History'),
        ('Heading 2', 'B. Current Law'),
        ('Heading 1', 'III. Argument'),
        ('Heading 2', 'A. Text'),
        ('Heading 2', 'B. Purpose'),
        ('Heading 1', 'IV. Conclusion')]
    footnotes = _part(text, 'word/footnotes.xml')
    assert 'First footnote in the introduction' in footnotes
    assert 'First footnote in the history section' in footnotes
    # The Bluebook citation style turns citations into footnotes.
    assert 'Antonin Scalia' in footnotes
    assert 'A Matter of Interpretation' in footnotes
    paragraphs = [p.text for p in docx.Document(str(text)).paragraphs]
    assert not any('Scalia' in paragraph for paragraph in paragraphs)
    document = docx.Document(str(text))
    assert document.styles['Normal'].font.name == 'Times New Roman'
    assert _slides(slides)[1:] == [
        ('Section Header', 'III. Argument'),
        ('Title and Content', 'The Argument')]


def test_word_template_from_project(law_review_project: pathlib.Path) -> None:
    """Tests that a Word template in the project folder is used."""
    template = law_review_project / 'house.docx'
    house = docx.Document()
    house.styles['Normal'].font.name = 'Courier New'
    house.save(str(template))
    project_file = law_review_project / 'project.toml'
    project_file.write_text(
        project_file.read_text(encoding = 'utf-8').replace(
            '[project]', '[project]\ntext_template = "house"'),
        encoding = 'utf-8')
    path = coursebook.build(law_review_project, include = ['text'])[0]
    assert docx.Document(str(path)).styles['Normal'].font.name == 'Courier New'


def test_output_folder_override(
        coursebook_project: pathlib.Path,
        tmp_path: pathlib.Path) -> None:
    """Tests building into another folder."""
    paths = coursebook.build(
        coursebook_project, include = ['text'],
        output_folder = tmp_path / 'elsewhere')
    assert paths == [tmp_path / 'elsewhere' / 'crazy_idea.docx']
    assert paths[0].is_file()


def test_project_without_outline(tmp_path: pathlib.Path) -> None:
    """Tests that a project needs outline entries."""
    (tmp_path / 'project.ini').write_text(
        '[Project]\nName: Empty\n', encoding = 'utf-8')
    with pytest.raises(ValueError, match = 'no outline entries'):
        coursebook.Project.from_folder(tmp_path)


def test_missing_bibliography(law_review_project: pathlib.Path) -> None:
    """Tests that a missing bibliography raises an error."""
    (law_review_project / 'references.bib').unlink()
    with pytest.raises(FileNotFoundError, match = 'references.bib'):
        coursebook.build(law_review_project)


def test_cli(
        coursebook_project: pathlib.Path,
        capsys: pytest.CaptureFixture[str]) -> None:
    """Tests building from the command line."""
    (coursebook_project / 'extra.md').write_text('Unused', encoding = 'utf-8')
    status = cli.main([
        str(coursebook_project), '--include', 'manuscript', '-v'])
    assert status == 0
    output = capsys.readouterr().out
    assert 'crazy_idea.docx' in output
    assert 'crazy_idea_slides' not in output


def test_cli_error(
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str]) -> None:
    """Tests that errors are reported without a traceback."""
    assert cli.main([str(tmp_path)]) == 1
    assert 'no project file' in capsys.readouterr().err


def _set_option(project: pathlib.Path, old: str, new: str) -> None:
    """Replaces text in the project file of a test project."""
    path = next(project.glob('project.*'))
    text = path.read_text(encoding = 'utf-8')
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding = 'utf-8')


def test_build_pdf_and_html(law_review_project: pathlib.Path) -> None:
    """Tests exporting the text to Word, PDF, and HTML at once."""
    _set_option(
        law_review_project, '[project]',
        '[project]\ntext_format = ["word", "pdf", "html"]')
    paths = coursebook.build(law_review_project, include = ['text'])
    assert [path.suffix for path in paths] == ['.docx', '.pdf', '.html']
    assert paths[1].read_bytes().startswith(b'%PDF')
    html = paths[2].read_text(encoding = 'utf-8')
    assert 'I. Introduction' in html
    assert 'First footnote in the history section' in html
    assert 'Antonin Scalia' in html
    assert 'text-transform: uppercase' in html


def test_html_embeds_images(coursebook_project: pathlib.Path) -> None:
    """Tests that HTML files include their images."""
    _set_option(
        coursebook_project, 'Output Folder', 'Text Format: html\nOutput Folder')
    path = coursebook.build(coursebook_project, include = ['text'])[0]
    html = path.read_text(encoding = 'utf-8')
    assert 'src="data:image/png;base64,' in html
    assert 'id="TOC"' in html


def test_slides_cannot_be_pdf(coursebook_project: pathlib.Path) -> None:
    """Tests that formats that cannot hold slides raise an error."""
    _set_option(
        coursebook_project, 'Output Folder',
        'Slides Format: pdf\nOutput Folder')
    with pytest.raises(ValueError, match = 'use powerpoint'):
        coursebook.build(coursebook_project, include = ['slides'])


def test_pdf_needs_typst(
        law_review_project: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests the error when the `typst` package is not installed."""
    monkeypatch.setitem(sys.modules, 'typst', None)
    _set_option(
        law_review_project, '[project]', '[project]\ntext_format = "pdf"')
    with pytest.raises(ImportError, match = 'coursebook\\[pdf\\]'):
        coursebook.build(law_review_project, include = ['text'])


def test_named_source_files(
        coursebook_project: pathlib.Path,
        caplog: pytest.LogCaptureFixture) -> None:
    """Tests outline entries with their own files and shared files."""
    chapters = coursebook_project / 'chapters'
    chapters.mkdir()
    (chapters / 'idea.md').write_text('From a subfolder.', encoding = 'utf-8')
    _set_option(
        coursebook_project, 'III: My Cool Idea',
        '-: Preface\nIII: My Cool Idea | chapters/idea.md')
    _set_option(
        coursebook_project, 'IV: Conclusion',
        'IV: Conclusion\nA: Introduction')
    with caplog.at_level(logging.WARNING):
        project = coursebook.Project.from_folder(coursebook_project)
    assert 'both use "introduction.md"' in caplog.text
    text = project.assemble('text')
    assert '# My Cool Idea\n\nFrom a subfolder.' in text
    assert '# Preface' in text
    assert [entry.file_name for entry in project.missing] == ['preface.md']
    assert [source.name for source in project.unused] == ['my_cool_idea']


def test_csl_from_settings(law_review_project: pathlib.Path) -> None:
    """Tests choosing an included citation style by name."""
    _set_option(
        law_review_project, '[project]',
        '[project]\ncsl = "bluebook-law-review"')
    _set_option(law_review_project, 'style = "law review"', 'style = "book"')
    path = coursebook.build(law_review_project, include = ['text'])[0]
    assert 'Antonin Scalia' in _part(path, 'word/footnotes.xml')


def test_csl_is_ignored_without_bibliography(
        coursebook_project: pathlib.Path) -> None:
    """Tests that a missing CSL file is not an error without citations."""
    _set_option(
        coursebook_project, 'Output Folder', 'CSL: missing.csl\nOutput Folder')
    assert coursebook.build(coursebook_project, include = ['text'])


def test_missing_csl(law_review_project: pathlib.Path) -> None:
    """Tests that a missing CSL file raises an error with citations."""
    _set_option(
        law_review_project, '[project]', '[project]\ncsl = "missing"')
    with pytest.raises(FileNotFoundError, match = 'bluebook-law-review'):
        coursebook.build(law_review_project, include = ['text'])


def test_cli_new_and_template(
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str]) -> None:
    """Tests creating a project and a template from the command line."""
    outline_file = tmp_path / 'outline.txt'
    outline_file.write_text(
        '# My outline\nI: Introduction\n\nII: Duty\n', encoding = 'utf-8')
    folder = tmp_path / 'torts'
    status = cli.main([
        'new', str(folder), '--name', 'Torts', '--style', 'book',
        '--format', 'toml', '--outline', str(outline_file),
        '--entry', '-: Appendix'])
    assert status == 0
    assert 'project.toml' in capsys.readouterr().out
    project = coursebook.Project.from_folder(folder)
    assert [entry.title for entry in project.outline] == [
        'Introduction', 'Duty', 'Appendix']
    assert cli.main(['build', str(folder), '-i', 'text']) == 0
    assert (folder / 'output' / 'torts.docx').is_file()
    assert cli.main(['new', str(folder)]) == 1
    assert 'already has a project file' in capsys.readouterr().err
    template = tmp_path / 'house.docx'
    assert cli.main(['template', 'law review', str(template)]) == 0
    assert template.is_file()
    assert cli.main(['template', 'memo', str(tmp_path / 'x.docx')]) == 1


def test_cli_default_project(
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    """Tests building the project in the current folder."""
    cli.main(['new', str(tmp_path), '-e', 'I: Only'])
    monkeypatch.chdir(tmp_path)
    assert cli.main([]) == 0
    assert 'slides' in capsys.readouterr().out
