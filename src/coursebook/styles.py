"""Styles that set how a `coursebook` project is formatted.

A style sets the default sections, heading labels, templates, citation style,
and formatting of a project. The "Style" setting of a project file chooses a
style by name. Names are matched without regard to case, spaces, or
underscores, so 'Law Review' chooses `LawReview`.

Every subclass of `Style` is registered automatically. So, to add a style,
subclass `Style` (or one of the styles here) and change its defaults:

```python
import dataclasses

import coursebook


@dataclasses.dataclass
class Seminar(coursebook.Coursebook):
    number_headings: bool = True
```

Contents:
    Book: style for a book with accompanying slides.
    Coursebook: style for a coursebook with slides and teaching notes.
    Formatting: formatting of the text and notes.
    LawReview: style for a law review article with accompanying slides.
    Style: base class for styles.
    get_style: returns the style with a name.

"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any, ClassVar

import wonka

from . import markdown

if TYPE_CHECKING:
    from . import outline


@dataclasses.dataclass
class Formatting:
    """Formatting of the text and notes.

    For Word files, the formatting is applied to pandoc's default Word
    template, so it is only used when a project does not name its own Word
    template. For PDF and HTML files, the formatting that those formats
    support is passed to pandoc's templates. A value of `None` keeps the
    formatting of pandoc's templates.

    Args:
        body_font: font for the text. Defaults to `None`.
        heading_font: font for headings and the title. Defaults to `None`,
            which uses `body_font`.
        font_size: size of the text in points. Defaults to `None`.
        line_spacing: spacing between the lines of the text, as a multiple of
            single spacing (such as 2.0 for double spacing). Defaults to
            `None`.
        first_line_indent: indent of the first line of each paragraph after
            the first one under a heading, in inches. Defaults to `None`.
        footnote_size: size of footnotes in points. Defaults to `None`.
        heading_color: color of headings and the title as a hexadecimal RGB
            value (such as '000000' for black). Defaults to `None`.
        center_top_headings: whether to center the top level headings.
            Defaults to `False`.
        capitalize_top_headings: whether to show the top level headings in
            capital letters. The text itself is not changed. Defaults to
            `False`.
        margins: the page margins on every side, in inches. Defaults to
            `None`.
        page_numbers: whether to put page numbers at the bottom of each page.
            Defaults to `False`.

    """

    body_font: str | None = None
    heading_font: str | None = None
    font_size: float | None = None
    line_spacing: float | None = None
    first_line_indent: float | None = None
    footnote_size: float | None = None
    heading_color: str | None = None
    center_top_headings: bool = False
    capitalize_top_headings: bool = False
    margins: float | None = None
    page_numbers: bool = False


@dataclasses.dataclass
class Style(wonka.AutoRegistrar):
    """Base class for styles.

    Args:
        sections: the sections to create files for when a project does not
            set "Include". Defaults to ('text', 'slides').
        number_headings: whether to put the outline labels in headings (such
            as 'I. Introduction'). Defaults to `False`.
        table_of_contents: whether to add a table of contents to the text and
            notes. Defaults to `False`.
        label_separator: text between an outline label and its title in a
            heading. Defaults to '. '.
        text_template: name or path of the Word template used when a project
            does not set one. Defaults to `None`, which uses pandoc's default
            template with `formatting` applied.
        slides_template: name or path of the PowerPoint template used when a
            project does not set one. Defaults to 'chalkboard'.
        csl: name or path of the citation style used when a project does not
            set one. Defaults to `None`, which uses pandoc's default (Chicago
            author-date).
        formatting: formatting of the text and notes. Defaults to a
            `Formatting` that keeps the formatting of pandoc's templates.

    Attributes:
        aliases: other names (in lower case with underscores) that choose this
            style.
        registry: every `Style` subclass, with keys that are the snake case
            names of the classes.

    """

    sections: tuple[str, ...] = ('text', 'slides')
    number_headings: bool = False
    table_of_contents: bool = False
    label_separator: str = '. '
    text_template: str | None = None
    slides_template: str | None = 'chalkboard'
    csl: str | None = None
    formatting: Formatting = dataclasses.field(
        default_factory = Formatting)
    aliases: ClassVar[tuple[str, ...]] = ()

    """ Public Methods """

    def format_heading(self, entry: outline.OutlineEntry) -> str:
        """Returns the heading text for an outline entry.

        Args:
            entry: the outline entry.

        Returns:
            The title of `entry`, after its label if `number_headings` is
                `True` and `entry` is numbered.

        """
        if self.number_headings and entry.numbered:
            return f'{entry.label}{self.label_separator}{entry.title}'
        return entry.title


@dataclasses.dataclass
class Book(Style):
    """Style for a book with accompanying slides.

    Args:
        sections: defaults to ('text', 'slides').
        number_headings: defaults to `False`.
        table_of_contents: defaults to `True`.
        label_separator: defaults to '. '.
        text_template: defaults to `None`.
        slides_template: defaults to 'chalkboard'.
        csl: defaults to `None`.
        formatting: defaults to Georgia at 11 points with 1.15 line spacing
            and page numbers.

    """

    table_of_contents: bool = True
    formatting: Formatting = dataclasses.field(
        default_factory = lambda: Formatting(
            body_font = 'Georgia',
            font_size = 11,
            line_spacing = 1.15,
            footnote_size = 9,
            page_numbers = True))


@dataclasses.dataclass
class Coursebook(Book):
    """Style for a coursebook with slides and teaching notes.

    Args:
        sections: defaults to ('text', 'slides', 'notes').
        number_headings: defaults to `False`.
        table_of_contents: defaults to `True`.
        label_separator: defaults to '. '.
        text_template: defaults to `None`.
        slides_template: defaults to 'chalkboard'.
        csl: defaults to `None`.
        formatting: defaults to Georgia at 11 points with 1.15 line spacing
            and page numbers.

    """

    sections: tuple[str, ...] = ('text', 'slides', 'notes')
    aliases: ClassVar[tuple[str, ...]] = ('casebook', 'textbook')


@dataclasses.dataclass
class LawReview(Style):
    """Style for a law review article with accompanying slides.

    Args:
        sections: defaults to ('text', 'slides').
        number_headings: defaults to `True`.
        table_of_contents: defaults to `False`.
        label_separator: defaults to '. '.
        text_template: defaults to `None`.
        slides_template: defaults to 'chalkboard'.
        csl: defaults to 'bluebook-law-review', which formats citations as
            Bluebook footnotes.
        formatting: defaults to double spaced Times New Roman at 12 points,
            with 10 point footnotes, centered, capitalized, black top level
            headings, one inch margins, and page numbers.

    """

    number_headings: bool = True
    csl: str | None = 'bluebook-law-review'
    formatting: Formatting = dataclasses.field(
        default_factory = lambda: Formatting(
            body_font = 'Times New Roman',
            font_size = 12,
            line_spacing = 2.0,
            first_line_indent = 0.5,
            footnote_size = 10,
            heading_color = '000000',
            center_top_headings = True,
            capitalize_top_headings = True,
            margins = 1.0,
            page_numbers = True))
    aliases: ClassVar[tuple[str, ...]] = ('law_review_article',)


""" Public Functions """


def get_style(name: str, **overrides: Any) -> Style:
    """Returns the style with `name`.

    Args:
        name: the name of a `Style` subclass or one of its aliases (such as
            'law review' or 'Coursebook').
        **overrides: values that replace the defaults of the style. Values
            of `None` are ignored.

    Returns:
        An instance of the style.

    Raises:
        ValueError: if no style has `name`.

    """
    key = markdown.normalize_name(name)
    choices: dict[str, type[Style]] = {}
    for registered_name, registered in Style.registry.items():
        choices[str(registered_name)] = registered
        for alias in registered.aliases:
            choices.setdefault(alias, registered)
    choices.pop('style', None)
    if key not in choices:
        known = ', '.join(sorted(choices))
        message = f'unknown style "{name}" (use one of: {known})'
        raise ValueError(message)
    kwargs = {
        field: value for field, value in overrides.items()
        if value is not None}
    return choices[key](**kwargs)
