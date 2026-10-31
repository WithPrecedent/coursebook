"""Tests for styles and exporters."""

from __future__ import annotations

import dataclasses
import pathlib

import pytest

import coursebook
from coursebook import outline


@pytest.mark.parametrize(('name', 'expected'), [
    ('law review', coursebook.LawReview),
    ('Law_Review', coursebook.LawReview),
    ('book', coursebook.Book),
    ('Coursebook', coursebook.Coursebook),
    ('textbook', coursebook.Coursebook)])
def test_get_style(name: str, expected: type[coursebook.Style]) -> None:
    """Tests choosing styles by name and alias."""
    assert type(coursebook.get_style(name)) is expected


def test_unknown_style() -> None:
    """Tests that an unknown style lists the known styles."""
    with pytest.raises(ValueError, match = 'law_review'):
        coursebook.get_style('memo')
    with pytest.raises(ValueError, match = 'unknown style'):
        coursebook.get_style('style')


def test_style_overrides() -> None:
    """Tests that overrides replace defaults and `None` is ignored."""
    style = coursebook.get_style(
        'law review', number_headings = False, table_of_contents = None)
    assert style.number_headings is False
    assert style.table_of_contents is False


def test_format_heading() -> None:
    """Tests headings with and without labels."""
    entry = outline.OutlineEntry(label = 'IV', title = 'Conclusion')
    assert coursebook.LawReview().format_heading(entry) == 'IV. Conclusion'
    assert coursebook.Book().format_heading(entry) == 'Conclusion'
    preface = outline.OutlineEntry(label = '', title = 'Preface')
    assert coursebook.LawReview().format_heading(preface) == 'Preface'


def test_custom_style_is_registered() -> None:
    """Tests that a subclass of `Style` can be chosen by name."""

    @dataclasses.dataclass
    class SeminarPaper(coursebook.Coursebook):
        number_headings: bool = True

    style = coursebook.get_style('Seminar Paper')
    assert isinstance(style, SeminarPaper)
    assert style.sections == ('text', 'slides', 'notes')


@pytest.mark.parametrize(('name', 'expected'), [
    ('word', coursebook.WordExporter),
    ('DOCX', coursebook.WordExporter),
    ('PowerPoint', coursebook.PowerPointExporter),
    ('pdf', coursebook.PdfExporter),
    ('HTML', coursebook.HtmlExporter),
    ('word_exporter', coursebook.WordExporter)])
def test_get_exporter(name: str, expected: type[coursebook.Exporter]) -> None:
    """Tests choosing exporters by name and alias."""
    assert type(coursebook.get_exporter(name)) is expected


def test_unknown_exporter() -> None:
    """Tests that an unknown format lists the known formats."""
    with pytest.raises(ValueError, match = 'powerpoint'):
        coursebook.get_exporter('epub')


def test_exporter_arguments(tmp_path: pathlib.Path) -> None:
    """Tests the pandoc arguments for each exporter."""
    options = coursebook.ExportOptions(
        template = tmp_path / 'reference.docx',
        resource_paths = [tmp_path],
        bibliography = [tmp_path / 'refs.bib'],
        csl = tmp_path / 'style.csl',
        table_of_contents = True)
    word = coursebook.WordExporter().get_arguments(options)
    assert f'--reference-doc={tmp_path / "reference.docx"}' in word
    assert '--citeproc' in word
    assert f'--csl={tmp_path / "style.csl"}' in word
    assert '--toc' in word
    slides = coursebook.PowerPointExporter().get_arguments(options)
    assert '--slide-level=2' in slides
    assert '--toc' not in slides


def test_formatting_metadata() -> None:
    """Tests the template variables for PDF and HTML files."""
    options = coursebook.ExportOptions(
        metadata = {'title': 'T'},
        formatting = coursebook.LawReview().formatting)
    pdf = coursebook.PdfExporter().get_metadata(options)
    assert pdf['mainfont'] == 'Times New Roman'
    assert pdf['fontsize'] == '12pt'
    assert pdf['margin'] == {'x': '1.0in', 'y': '1.0in'}
    assert pdf['page-numbering'] == '1'
    assert '#show heading.where(level: 1): upper' in pdf['header-includes']
    assert pdf['header-includes'].endswith('```\n')
    html = coursebook.HtmlExporter().get_metadata(options)
    assert html['mainfont'] == 'Times New Roman, serif'
    assert 'text-transform: uppercase' in html['header-includes']
    plain = coursebook.HtmlExporter().get_metadata(
        coursebook.ExportOptions(metadata = {'title': 'T'}))
    assert plain == {'title': 'T'}


def test_exporter_sections() -> None:
    """Tests which sections each exporter can export."""
    assert coursebook.PowerPointExporter.sections == ('slides',)
    for exporter in (
            coursebook.WordExporter, coursebook.PdfExporter,
            coursebook.HtmlExporter):
        assert exporter.sections == ('text', 'notes')
