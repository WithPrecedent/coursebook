"""Combines the source files of a project into a single markdown document.

The outline sets the order of the source files and adds a heading for each
entry. The headings inside each source file are moved beneath the heading of
its entry, and its footnote labels are made unique so that footnotes from
different files do not collide.

A source file's front matter may set:

* `title`: the title used in place of the outline title in headings.
* `visuals_in_notes`: whether to copy the images in its text into its notes
    (overriding the project setting).

Contents:
    assemble_document: combines one section of every source into a document.
    assemble_slides: combines the slides of every source into a slide deck.
    _MAXIMUM_HEADING_LEVEL: the deepest heading level that markdown supports.

"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from . import markdown

if TYPE_CHECKING:
    from collections.abc import Mapping

    from . import outline, sources, styles

_MAXIMUM_HEADING_LEVEL: int = 6


""" Public Functions """


def assemble_document(
        project_outline: outline.Outline,
        project_sources: Mapping[str, sources.Source],
        *,
        section: str,
        style: styles.Style,
        include_empty: bool = True,
        visuals_in_notes: bool = False) -> str:
    """Combines one section of every source into a markdown document.

    Each outline entry becomes a heading at the level of the entry (so a top
    level entry is a level one heading). The headings in each source are
    moved beneath the heading of its entry.

    Args:
        project_outline: the outline of the project.
        project_sources: the sources of the project, with keys that are the
            names of the outline entries.
        section: the section to combine ('text' or 'notes').
        style: the style of the project.
        include_empty: whether to add headings for entries that have no
            content in `section` (and no entries beneath them with content).
            Defaults to `True`.
        visuals_in_notes: whether to copy the images in the text of each
            source into its notes when `section` is 'notes'. A source's front
            matter may override this. Defaults to `False`.

    Returns:
        The combined markdown.

    """
    parts: list[str] = []
    for entry in project_outline.walk():
        if not include_empty and not _has_content(
                entry, project_sources, section, visuals_in_notes):
            continue
        source = project_sources.get(entry.name)
        level = min(entry.level + 1, _MAXIMUM_HEADING_LEVEL)
        heading = style.format_heading(_titled(entry, source))
        parts.append(f'{"#" * level} {heading}')
        body = _get_body(source, section, visuals_in_notes)
        if body:
            body = markdown.namespace_footnotes(body, prefix = entry.name)
            parts.append(markdown.shift_headings(body, levels = level))
    return _join(parts)


def assemble_slides(
        project_outline: outline.Outline,
        project_sources: Mapping[str, sources.Source],
        *,
        style: styles.Style,
        section_slides: bool = True) -> str:
    """Combines the slides of every source into a markdown slide deck.

    The deck uses pandoc's slide level 2: each level two heading (or
    horizontal rule) starts a new slide and each level one heading is a
    section title slide. In a source file, each slide starts with a level one
    heading (which becomes level two) or a horizontal rule ('---'). If the
    slides of a source do not start with a heading, the first slide is given
    the heading of its entry.

    Args:
        project_outline: the outline of the project.
        project_sources: the sources of the project, with keys that are the
            names of the outline entries.
        style: the style of the project.
        section_slides: whether to add a section title slide for each entry
            that has slides (or entries beneath it with slides). Defaults to
            `True`.

    Returns:
        The combined markdown.

    """
    parts: list[str] = []
    for entry in project_outline.walk():
        if not _has_content(entry, project_sources, 'slides'):
            continue
        source = project_sources.get(entry.name)
        heading = style.format_heading(_titled(entry, source))
        if section_slides:
            parts.append(f'# {heading}')
        body = _get_body(source, 'slides')
        if body:
            if not body.lstrip().startswith('#'):
                parts.append(f'## {heading}')
            body = markdown.namespace_footnotes(body, prefix = entry.name)
            parts.append(markdown.shift_headings(body, levels = 1))
    return _join(parts)


""" Private Functions """


def _get_body(
        source: sources.Source | None,
        section: str,
        visuals_in_notes: bool = False) -> str:
    """Returns the markdown of `section` in `source`.

    Args:
        source: the source file, or `None` if the entry has no source file.
        section: the section to return.
        visuals_in_notes: whether to add the images in the text of `source`
            to its notes when `section` is 'notes'. The front matter of
            `source` may override this. Defaults to `False`.

    Returns:
        The markdown of the section, or an empty `str` if there is none.

    """
    if source is None:
        return ''
    body = source.get(section)
    copy_visuals = bool(source.metadata.get(
        'visuals_in_notes', visuals_in_notes))
    if section == 'notes' and copy_visuals:
        images = markdown.extract_images(source.get('text'))
        body = '\n\n'.join(part for part in (body, *images) if part)
    return body


def _has_content(
        entry: outline.OutlineEntry,
        project_sources: Mapping[str, sources.Source],
        section: str,
        visuals_in_notes: bool = False) -> bool:
    """Returns whether `entry` or an entry beneath it has `section` content.

    Args:
        entry: the outline entry.
        project_sources: the sources of the project.
        section: the section to check.
        visuals_in_notes: whether images in the text count as notes. Defaults
            to `False`.

    Returns:
        Whether there is any content in `section` for `entry` or the entries
            beneath it.

    """
    return any(
        _get_body(project_sources.get(item.name), section, visuals_in_notes)
        for item in entry.walk())


def _join(parts: list[str]) -> str:
    """Joins the parts of a markdown document.

    Args:
        parts: the headings and bodies of the document, in order.

    Returns:
        The parts separated by blank lines, with a final newline.

    """
    return '\n\n'.join(parts) + '\n' if parts else ''


def _titled(
        entry: outline.OutlineEntry,
        source: sources.Source | None) -> outline.OutlineEntry:
    """Returns `entry` with the title from the front matter of `source`.

    Args:
        entry: the outline entry.
        source: the source file of `entry`, if any.

    Returns:
        `entry`, or a copy with its title replaced if the front matter of
            `source` sets `title`.

    """
    if source is not None and source.metadata.get('title'):
        return dataclasses.replace(
            entry, title = str(source.metadata['title']))
    return entry
