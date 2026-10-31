"""Tools for reading and adjusting the markdown in source files.

Contents:
    extract_images: returns the images in markdown text.
    namespace_footnotes: adds a prefix to the footnote labels in markdown text.
    normalize_name: converts a name to lower case words joined by underscores.
    shift_headings: changes the level of every heading in markdown text.
    split_front_matter: separates the front matter from markdown text.
    split_sections: divides markdown text into its marked sections.
    _DIVIDER: matches a line that opens or closes a section (such as
        '<slides>').
    _FENCE: matches the opening or closing line of a fenced code block.
    _FOOTNOTE: matches a footnote reference or definition label.
    _FRONT_MATTER_DELIMITERS: the lines that may open and close front matter.
    _HEADING: matches the '#' characters at the start of an ATX heading.
    _IMAGE: matches a markdown image and any pandoc attributes after it.
    _MAXIMUM_HEADING_LEVEL: the deepest heading level that markdown supports.

"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from collections.abc import Iterator

_FENCE: re.Pattern[str] = re.compile(r'^ {0,3}(`{3,}|~{3,})')
# Front matter normally opens with '---'. The `'''` delimiter is also allowed
# because the original `coursebook` examples used it.
_FRONT_MATTER_DELIMITERS: dict[str, tuple[str, ...]] = {
    '---': ('---', '...'),
    "'''": ("'''",)}
_DIVIDER: re.Pattern[str] = re.compile(
    r'^\s*<\s*(/?)\s*([A-Za-z_]+)\s*>\s*$')
_FOOTNOTE: re.Pattern[str] = re.compile(r'\[\^([^\]\s]+)\]')
_HEADING: re.Pattern[str] = re.compile(r'^(#{1,6})(?=\s|$)')
_IMAGE: re.Pattern[str] = re.compile(
    r'!\[[^\]]*\]\([^)]+\)(?:\{[^}]*\})?')
_MAXIMUM_HEADING_LEVEL: int = 6


""" Public Functions """


def extract_images(text: str) -> list[str]:
    """Returns the images in markdown `text`.

    Images inside fenced code blocks are ignored.

    Args:
        text: markdown text.

    Returns:
        The markdown for each image (including any pandoc attributes, such as
            `{width=50%}`), in the order in which they appear.

    """
    images: list[str] = []
    for line, in_code in _iterate_lines(text):
        if not in_code:
            images.extend(match.group(0) for match in _IMAGE.finditer(line))
    return images


def namespace_footnotes(text: str, prefix: str) -> str:
    """Adds `prefix` to the footnote labels in markdown `text`.

    Pandoc treats footnote labels as belonging to the whole document. So, if two
    source files each use `[^1]`, the second footnote would be replaced by the
    first when the files are combined. Adding a prefix that is unique to each
    source file keeps the footnotes separate.

    Args:
        text: markdown text.
        prefix: text to add to the start of each footnote label.

    Returns:
        `text` with each footnote label (in both the references and the
            definitions) changed from `[^label]` to `[^prefix-label]`.

    """
    lines = []
    for line, in_code in _iterate_lines(text):
        lines.append(
            line if in_code else _FOOTNOTE.sub(rf'[^{prefix}-\1]', line))
    return '\n'.join(lines)


def normalize_name(name: str) -> str:
    """Converts `name` to lower case words joined by underscores.

    Every run of characters that are not letters or numbers is replaced with a
    single underscore. For example, 'Law & Economics' becomes 'law_economics'
    and 'Law Review' becomes 'law_review'.

    Args:
        name: the name to convert.

    Returns:
        The normalized name.

    """
    return re.sub(r'[^0-9a-z]+', '_', name.lower()).strip('_')


def shift_headings(text: str, levels: int) -> str:
    """Changes the level of every heading in markdown `text`.

    Only ATX headings (headings that start with '#') are changed. Headings
    inside fenced code blocks are left alone. Markdown does not support more
    than six levels of headings, so deeper headings are kept at level six.

    Args:
        text: markdown text.
        levels: number of levels to add to each heading. A negative number
            raises the headings, but never above level one.

    Returns:
        `text` with its headings shifted.

    """
    lines = []
    for line, in_code in _iterate_lines(text):
        match = None if in_code else _HEADING.match(line)
        if match:
            level = len(match.group(1)) + levels
            level = max(1, min(level, _MAXIMUM_HEADING_LEVEL))
            lines.append('#' * level + line[match.end():])
        else:
            lines.append(line)
    return '\n'.join(lines)


def split_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """Separates the YAML front matter from markdown `text`.

    Front matter must start on the first line that is not blank. It opens with
    '---' (and closes with '---' or '...') or opens and closes with "'''".

    Args:
        text: markdown text that may start with front matter.

    Returns:
        The front matter as a `dict` (which is empty if there is no front
            matter) and the rest of `text`.

    Raises:
        ValueError: if the front matter is never closed or is not a mapping of
            keys to values.

    """
    lines = text.lstrip('﻿').splitlines()
    start = 0
    while start < len(lines) and not lines[start].strip():
        start += 1
    if start == len(lines):
        return {}, ''
    opener = lines[start].strip()
    if opener not in _FRONT_MATTER_DELIMITERS:
        return {}, text
    closers = _FRONT_MATTER_DELIMITERS[opener]
    for end in range(start + 1, len(lines)):
        if lines[end].strip() in closers:
            break
    else:
        message = f'front matter opened with "{opener}" is never closed'
        raise ValueError(message)
    metadata = yaml.safe_load('\n'.join(lines[start + 1:end]))
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        message = 'front matter must be a mapping of keys to values'
        raise ValueError(message)  # noqa: TRY004
    return metadata, '\n'.join(lines[end + 1:])


def split_sections(
        text: str,
        names: dict[str, str],
        default: str) -> dict[str, str]:
    """Divides markdown `text` into the sections marked by dividers.

    A divider is a line with only a section name inside '<' and '>' (such as
    '<slides>'). The text after a divider, up to the next divider, belongs to
    that section. Text before the first divider belongs to the `default`
    section. A closing divider (such as '</slides>') returns to the `default`
    section. Dividers inside fenced code blocks are ignored. If a section
    appears more than once, its parts are joined in order.

    Args:
        text: markdown text without front matter.
        names: `dict` with keys that are the names that may appear in dividers
            (in lower case) and values that are the sections they mark. This
            allows more than one name for a section (such as 'manuscript' for
            'text').
        default: the section for text that is not after a divider.

    Returns:
        A `dict` with keys that are section names and values that are the
            stripped text of each section. Only sections with text are included.

    Raises:
        ValueError: if a divider names a section that is not in `names`.

    """
    parts: dict[str, list[str]] = {}
    current = default
    for line, in_code in _iterate_lines(text):
        match = None if in_code else _DIVIDER.match(line)
        if match:
            closing, name = match.groups()
            if name.lower() not in names:
                known = ', '.join(f'<{key}>' for key in names)
                message = f'unknown divider "{line.strip()}" (use {known})'
                raise ValueError(message)
            current = default if closing else names[name.lower()]
            parts.setdefault(current, []).append('')
            continue
        parts.setdefault(current, []).append(line)
    sections = {}
    for name, lines in parts.items():
        section = '\n'.join(lines).strip('\n')
        if section.strip():
            sections[name] = section
    return sections


""" Private Functions """


def _iterate_lines(text: str) -> Iterator[tuple[str, bool]]:
    """Yields each line of `text` and whether it is in a fenced code block.

    The opening and closing lines of a fenced code block count as being in the
    code block.

    Args:
        text: markdown text.

    Yields:
        Each line of `text` and whether that line is part of a fenced code
            block.

    """
    fence: str | None = None
    for line in text.split('\n'):
        match = _FENCE.match(line)
        if fence is None and match:
            fence = match.group(1)
            yield line, True
        elif fence is not None:
            if (
                    match
                    and match.group(1)[0] == fence[0]
                    and len(match.group(1)) >= len(fence)
                    and not line.strip()[len(match.group(1)):].strip()):
                fence = None
            yield line, True
        else:
            yield line, False
