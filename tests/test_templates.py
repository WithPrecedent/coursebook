"""Tests for finding and preparing Office templates."""

from __future__ import annotations

import pathlib
import shutil
import zipfile

import docx
import pptx
import pytest
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt

import coursebook
from coursebook import templates


def test_list_templates() -> None:
    """Tests listing the included templates."""
    assert templates.list_templates('powerpoint') == ['chalkboard']
    assert templates.list_templates('word') == []


def test_find_included_template(tmp_path: pathlib.Path) -> None:
    """Tests finding an included template by name."""
    path = templates.find_template('chalkboard', 'powerpoint', tmp_path)
    assert path.name == 'chalkboard.thmx'


def test_project_template_comes_first(tmp_path: pathlib.Path) -> None:
    """Tests that a template in the project folder is found first."""
    included = templates.find_template('chalkboard', 'powerpoint', tmp_path)
    copy = shutil.copy(included, tmp_path / 'chalkboard.thmx')
    assert templates.find_template('chalkboard', 'powerpoint', tmp_path) == (
        pathlib.Path(copy))
    assert templates.find_template(
        'chalkboard.thmx', 'powerpoint', tmp_path) == pathlib.Path(copy)


def test_missing_template(tmp_path: pathlib.Path) -> None:
    """Tests that a missing template lists the included templates."""
    with pytest.raises(FileNotFoundError, match = 'chalkboard'):
        templates.find_template('whiteboard', 'powerpoint', tmp_path)
    with pytest.raises(FileNotFoundError, match = 'not found'):
        templates.find_template('house.docx', 'word', tmp_path)


def test_wrong_template_type(tmp_path: pathlib.Path) -> None:
    """Tests a template with the wrong extension or application."""
    with pytest.raises(ValueError, match = 'not a word template'):
        templates.find_template('deck.pptx', 'word', tmp_path)
    with pytest.raises(ValueError, match = 'unknown application'):
        templates.find_template('deck', 'excel', tmp_path)
    with pytest.raises(ValueError, match = 'not a Word or PowerPoint'):
        templates.prepare_template(tmp_path / 'sheet.xltx', tmp_path)


def test_convert_theme(tmp_path: pathlib.Path) -> None:
    """Tests converting the chalkboard Office theme to a presentation."""
    theme = templates.find_template('chalkboard', 'powerpoint', tmp_path)
    path = templates.prepare_template(theme, tmp_path)
    assert path.suffix == '.pptx'
    presentation = pptx.Presentation(str(path))
    names = {layout.name for layout in presentation.slide_layouts}
    # Pandoc needs these layouts.
    assert {
        'Title Slide', 'Title and Content', 'Section Header', 'Two Content',
        'Comparison', 'Content with Caption', 'Blank'} <= names


def test_theme_without_presentation(tmp_path: pathlib.Path) -> None:
    """Tests that a theme without a slide master raises an error."""
    path = tmp_path / 'colors.thmx'
    with zipfile.ZipFile(path, 'w') as theme:
        theme.writestr('theme/theme/theme1.xml', '<a:theme/>')
    with pytest.raises(ValueError, match = 'slide master'):
        templates.prepare_template(path, tmp_path)


def test_convert_office_templates(tmp_path: pathlib.Path) -> None:
    """Tests converting '.dotx' and '.potx' templates."""
    pairs = (('docx', 'dotx', 'wordprocessingml'),
             ('pptx', 'potx', 'presentationml'))
    for document, template, kind in pairs:
        source = tmp_path / f'house.{template}'
        main = f'application/vnd.openxmlformats-officedocument.{kind}'
        with zipfile.ZipFile(source, 'w') as package:
            package.writestr(
                '[Content_Types].xml',
                f'<Types>{main}.template.main+xml</Types>')
        converted = templates.prepare_template(source, tmp_path / 'out')
        assert converted.suffix == f'.{document}'
        with zipfile.ZipFile(converted) as package:
            types = package.read('[Content_Types].xml').decode()
        assert 'template.main' not in types


def test_documents_are_used_as_is(tmp_path: pathlib.Path) -> None:
    """Tests that '.docx' and '.pptx' files are not converted."""
    path = tmp_path / 'house.docx'
    assert templates.prepare_template(path, tmp_path / 'out') == path


def test_create_word_template(tmp_path: pathlib.Path) -> None:
    """Tests applying the law review formatting to a Word template."""
    path = templates.create_word_template(
        coursebook.LawReview().formatting, tmp_path / 'reference.docx')
    document = docx.Document(str(path))
    normal = document.styles['Normal']
    assert normal.font.name == 'Times New Roman'
    assert normal.font.size == Pt(12)
    assert document.styles['Body Text'].paragraph_format.line_spacing == 2.0
    assert document.styles['Footnote Text'].font.size == Pt(10)
    heading = document.styles['Heading 1']
    assert heading.font.name == 'Times New Roman'
    assert heading.font.all_caps is True
    assert heading.paragraph_format.alignment == WD_ALIGN_PARAGRAPH.CENTER
    assert str(heading.font.color.rgb) == '000000'
    fonts = heading.element.rPr.find(qn('w:rFonts'))
    assert fonts.get(qn('w:asciiTheme')) is None


def test_empty_formatting_keeps_pandoc_template(tmp_path: pathlib.Path) -> None:
    """Tests that empty formatting keeps pandoc's fonts."""
    path = templates.create_word_template(
        coursebook.Formatting(), tmp_path / 'reference.docx')
    document = docx.Document(str(path))
    assert document.styles['Normal'].font.name is None
    fonts = document.styles['Heading 1'].element.rPr.find(qn('w:rFonts'))
    assert fonts.get(qn('w:asciiTheme')) == 'majorHAnsi'


def test_word_template_page_layout(tmp_path: pathlib.Path) -> None:
    """Tests margins, page numbers, and continuous footnote numbers."""
    path = templates.create_word_template(
        coursebook.LawReview().formatting, tmp_path / 'reference.docx')
    document = docx.Document(str(path))
    section = document.sections[0]
    assert section.left_margin.inches == 1.0
    assert section.top_margin.inches == 1.0
    footer = section.footer.paragraphs[0]._p.xml
    assert 'PAGE' in footer
    properties = section._sectPr.find(qn('w:footnotePr'))
    restart = properties.find(qn('w:numRestart'))
    assert restart.get(qn('w:val')) == 'continuous'


def test_find_included_csl(tmp_path: pathlib.Path) -> None:
    """Tests finding the included Bluebook citation style."""
    assert templates.list_templates('csl') == ['bluebook-law-review']
    path = templates.find_template('bluebook-law-review', 'csl', tmp_path)
    assert path.suffix == '.csl'
    assert 'class="note"' in path.read_text(encoding = 'utf-8')
