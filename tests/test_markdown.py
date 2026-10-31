"""Tests for the markdown helpers and source files."""

from __future__ import annotations

import pathlib

import pytest

from coursebook import markdown, settings, sources

FENCE: str = '```'


def test_front_matter_with_dashes() -> None:
    """Tests front matter between '---' lines."""
    metadata, body = markdown.split_front_matter(
        '\n---\ntitle: Facts\nvisuals_in_notes: yes\n---\nBody\n')
    assert metadata == {'title': 'Facts', 'visuals_in_notes': True}
    assert body.strip() == 'Body'


def test_front_matter_with_quotes() -> None:
    """Tests front matter between "'''" lines and empty front matter."""
    metadata, body = markdown.split_front_matter("'''\n\n'''\n\nBody")
    assert metadata == {}
    assert body.strip() == 'Body'


def test_no_front_matter() -> None:
    """Tests that text without front matter is returned unchanged."""
    text = 'Body\n---\nmore'
    assert markdown.split_front_matter(text) == ({}, text)


def test_unclosed_front_matter() -> None:
    """Tests that front matter must be closed."""
    with pytest.raises(ValueError, match = 'never closed'):
        markdown.split_front_matter('---\ntitle: x\n')


def test_front_matter_must_be_mapping() -> None:
    """Tests that front matter must be a mapping."""
    with pytest.raises(ValueError, match = 'mapping'):
        markdown.split_front_matter('---\n- a\n- b\n---\n')


def test_split_sections() -> None:
    """Tests dividers, the default section, and repeated sections."""
    text = (
        'Opening text.\n\n<slides>\n# Slide\n\n<NOTES>\nA note.\n\n'
        '</notes>\nMore text.\n\n< text >\nLast text.')
    sections = markdown.split_sections(
        text, names = settings.SECTION_ALIASES, default = 'text')
    assert sections['slides'] == '# Slide'
    assert sections['notes'] == 'A note.'
    assert sections['text'] == 'Opening text.\n\n\nMore text.\n\n\nLast text.'


def test_split_sections_skips_empty_sections() -> None:
    """Tests that sections with only blank lines are left out."""
    sections = markdown.split_sections(
        '\n<text>\n\n\n<slides>\n\n',
        names = settings.SECTION_ALIASES,
        default = 'text')
    assert sections == {}


def test_split_sections_manuscript_alias() -> None:
    """Tests that '<manuscript>' marks the text."""
    sections = markdown.split_sections(
        '<manuscript>\nWords', names = settings.SECTION_ALIASES,
        default = 'text')
    assert sections == {'text': 'Words'}


def test_dividers_in_code_are_ignored() -> None:
    """Tests that dividers inside fenced code blocks are not dividers."""
    text = f'Text\n{FENCE}\n<slides>\n{FENCE}\n<slides>\nSlide'
    sections = markdown.split_sections(
        text, names = settings.SECTION_ALIASES, default = 'text')
    assert sections['text'] == f'Text\n{FENCE}\n<slides>\n{FENCE}'
    assert sections['slides'] == 'Slide'


def test_unknown_divider() -> None:
    """Tests that unknown dividers raise an error."""
    with pytest.raises(ValueError, match = 'unknown divider'):
        markdown.split_sections(
            '<handouts>\n', names = settings.SECTION_ALIASES,
            default = 'text')


def test_shift_headings() -> None:
    """Tests shifting headings, including code blocks and limits."""
    text = f'# One\n#hashtag\n{FENCE}\n# code\n{FENCE}\n##### Five\n#'
    shifted = markdown.shift_headings(text, levels = 2)
    assert shifted.split('\n') == [
        '### One', '#hashtag', FENCE, '# code', FENCE, '###### Five', '###']
    assert markdown.shift_headings('### Three', levels = -5) == '# Three'


def test_namespace_footnotes() -> None:
    """Tests that footnote labels get a prefix outside code."""
    text = f'Claim.[^1] Inline.^[note]\n\n[^1]: Note.\n{FENCE}\n[^1]\n{FENCE}'
    namespaced = markdown.namespace_footnotes(text, prefix = 'intro')
    assert namespaced.split('\n') == [
        'Claim.[^intro-1] Inline.^[note]', '', '[^intro-1]: Note.', FENCE,
        '[^1]', FENCE]


def test_extract_images() -> None:
    """Tests finding images and their attributes."""
    text = (
        'See ![A chart](chart.png){width=50%} and ![](b.jpg).\n'
        f'{FENCE}\n![code](c.png)\n{FENCE}')
    assert markdown.extract_images(text) == [
        '![A chart](chart.png){width=50%}', '![](b.jpg)']


@pytest.mark.parametrize(('name', 'expected'), [
    ('Interesting Premise 1', 'interesting_premise_1'),
    ('Law & Economics', 'law_economics'),
    ('  Law Review  ', 'law_review'),
    ('law_review', 'law_review')])
def test_normalize_name(name: str, expected: str) -> None:
    """Tests normalizing names for files and settings."""
    assert markdown.normalize_name(name) == expected


def test_source_from_file(tmp_path: pathlib.Path) -> None:
    """Tests loading a source file."""
    path = tmp_path / 'My Idea.md'
    path.write_text(
        '---\ntitle: Better Title\n---\nText\n<slides>\n# Slide\n',
        encoding = 'utf-8')
    source = sources.Source.from_file(path)
    assert source.name == 'my_idea'
    assert source.metadata == {'title': 'Better Title'}
    assert source.get('text') == 'Text'
    assert source.get('slides') == '# Slide'
    assert source.get('notes') == ''


def test_source_errors_name_the_file(tmp_path: pathlib.Path) -> None:
    """Tests that errors in a source file name the file."""
    (tmp_path / 'broken.md').write_text('<handout>\n', encoding = 'utf-8')
    with pytest.raises(ValueError, match = 'broken.md'):
        sources.load_sources(tmp_path)


def test_duplicate_sources(tmp_path: pathlib.Path) -> None:
    """Tests that two files for the same entry raise an error."""
    (tmp_path / 'My_Idea.md').write_text('a', encoding = 'utf-8')
    (tmp_path / 'my idea.md').write_text('b', encoding = 'utf-8')
    with pytest.raises(ValueError, match = 'same outline entry'):
        sources.load_sources(tmp_path)
