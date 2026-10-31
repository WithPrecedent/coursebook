"""Tests for outlines."""

from __future__ import annotations

import logging

import pytest

from coursebook import outline

README_OUTLINE: list[str] = [
    'I: Introduction',
    'II: Literature Review',
    'III: My Cool Idea',
    'A: Interesting Premise 1',
    '1: Underlying Facts',
    '2: Supporting Work',
    'B: Interesting Premise 2',
    'IV: Conclusion']


def _levels(project_outline: outline.Outline) -> list[tuple[str, int]]:
    """Returns the label and level of each entry."""
    return [(entry.label, entry.level) for entry in project_outline]


def test_readme_outline() -> None:
    """Tests the outline from the README."""
    project_outline = outline.Outline.from_lines(README_OUTLINE)
    assert _levels(project_outline) == [
        ('I', 0), ('II', 0), ('III', 0), ('A', 1), ('1', 2), ('2', 2),
        ('B', 1), ('IV', 0)]
    assert len(project_outline) == 8
    assert len(project_outline.entries) == 4
    idea = project_outline.entries[2]
    assert [child.title for child in idea.children] == [
        'Interesting Premise 1', 'Interesting Premise 2']
    assert idea.children[0].children[0].name == 'underlying_facts'


def test_repeated_labels() -> None:
    """Tests that labels may repeat under different parents."""
    project_outline = outline.Outline.from_lines([
        'I: One', 'A: First', 'B: Second', 'II: Two', 'A: Third', 'B: Fourth'])
    assert _levels(project_outline) == [
        ('I', 0), ('A', 1), ('B', 1), ('II', 0), ('A', 1), ('B', 1)]
    assert [len(entry.children) for entry in project_outline.entries] == [2, 2]


def test_deep_outline() -> None:
    """Tests all five kinds of labels."""
    project_outline = outline.Outline.from_lines([
        'I: a', 'A: b', '1: c', 'a: d', 'i: e', 'ii: f', 'b: g', '2: h'])
    assert [entry.level for entry in project_outline] == [
        0, 1, 2, 3, 4, 4, 3, 2]


def test_arabic_top_level() -> None:
    """Tests a book outline that numbers chapters with Arabic numbers."""
    project_outline = outline.Outline.from_lines([
        '1: Chapter', 'A: Part', 'B: Part', '2: Chapter', '3: Chapter'])
    assert [entry.level for entry in project_outline] == [0, 1, 1, 0, 0]


def test_letter_i_after_h() -> None:
    """Tests that 'i' after 'h' continues the letters."""
    lines = ['I: x', 'A: x', '1: x'] + [
        f'{letter}: x' for letter in 'abcdefghi']
    levels = [entry.level for entry in outline.Outline.from_lines(lines)]
    assert levels[-1] == 3


def test_upper_i_after_h() -> None:
    """Tests that 'I' after 'H' is a letter, not a Roman numeral."""
    lines = ['I: x'] + [f'{letter}: x' for letter in 'ABCDEFGHI']
    levels = [entry.level for entry in outline.Outline.from_lines(lines)]
    assert levels[-1] == 1


def test_label_punctuation() -> None:
    """Tests labels with periods and parentheses."""
    project_outline = outline.Outline.from_lines([
        'I.: One', '(A): Part', 'B) = Part: With Colon'])
    assert _levels(project_outline) == [('I', 0), ('A', 1), ('B', 1)]
    assert project_outline.entries[0].children[1].title == 'Part: With Colon'


def test_tuples_and_blank_lines() -> None:
    """Tests label and title pairs and blank lines."""
    project_outline = outline.Outline.from_lines(['', ('I.', ' One '), '  '])
    assert [(entry.label, entry.title) for entry in project_outline] == [
        ('I', 'One')]


def test_skipped_label_warns(caplog: pytest.LogCaptureFixture) -> None:
    """Tests that skipping labels warns but still places the entry."""
    with caplog.at_level(logging.WARNING):
        project_outline = outline.Outline.from_lines(['I: x', 'A: x', 'C: x'])
    assert _levels(project_outline) == [('I', 0), ('A', 1), ('C', 1)]
    assert 'skips labels' in caplog.text


def test_double_letters() -> None:
    """Tests that labels after 'Z' double the letter."""
    lines = ['I: x'] + [f'{chr(65 + n)}: x' for n in range(26)] + ['AA: x']
    levels = [entry.level for entry in outline.Outline.from_lines(lines)]
    assert levels[-1] == 1


@pytest.mark.parametrize('lines', [
    ['A: x', 'A: y'],
    ['I: x', 'Q7: y'],
    ['B: x']])
def test_invalid_labels(lines: list[str]) -> None:
    """Tests labels that cannot be placed."""
    with pytest.raises(ValueError, match = 'cannot place'):
        outline.Outline.from_lines(lines)


@pytest.mark.parametrize('line', ['Introduction', ': Title', 'I:  '])
def test_invalid_lines(line: str) -> None:
    """Tests outline lines without a label or title."""
    with pytest.raises(ValueError, match = 'label and a title'):
        outline.parse_outline_line(line)


def test_unnumbered_entries() -> None:
    """Tests that unnumbered entries keep the numbering going."""
    project_outline = outline.Outline.from_lines([
        '-: Preface', '--: Thanks', 'I: Intro', 'A: Part', '-: Interlude',
        'II: Two', 'A: x', '--: Aside', 'B: y', '-: Appendix', 'A: Data',
        'III: Three'])
    assert [(entry.label, entry.level) for entry in project_outline] == [
        ('', 0), ('', 1), ('I', 0), ('A', 1), ('', 0), ('II', 0), ('A', 1),
        ('', 1), ('B', 1), ('', 0), ('A', 1), ('III', 0)]
    assert not project_outline.entries[0].numbered
    assert project_outline.entries[1].numbered


def test_unnumbered_entry_too_deep() -> None:
    """Tests that an unnumbered entry cannot skip a level."""
    with pytest.raises(ValueError, match = 'more than one level'):
        outline.Outline.from_lines(['I: One', '---: Too Deep'])


def test_entry_files() -> None:
    """Tests outline entries that name their source files."""
    project_outline = outline.Outline.from_lines([
        'I: Introduction | chapters/Intro Chapter.md',
        ('II', 'Law | Economics'),
        ('III', 'Three', 'three.MD'),
        'IV: Four | not a file'])
    entries = list(project_outline)
    assert entries[0].title == 'Introduction'
    assert entries[0].file == 'chapters/Intro Chapter.md'
    assert entries[0].name == 'chapters_intro_chapter'
    assert entries[0].file_name == 'chapters/Intro Chapter.md'
    assert entries[1].title == 'Law | Economics'
    assert entries[1].file is None
    assert entries[1].file_name == 'law_economics.md'
    assert entries[2].file == 'three.MD'
    assert entries[3].title == 'Four | not a file'


def test_too_many_parts() -> None:
    """Tests a tuple with too many parts."""
    with pytest.raises(ValueError, match = 'label and a title'):
        outline.Outline.from_lines([('I', 'One', 'one.md', 'extra')])
