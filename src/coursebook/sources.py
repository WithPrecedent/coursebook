"""The markdown source files of a `coursebook` project.

Each source file holds the content for one entry in the outline. It may start
with YAML front matter and is divided into sections by lines such as '<text>',
'<slides>', and '<notes>'. Content before the first divider belongs to the
text.

Contents:
    Source: the front matter and sections of a source file.
    load_sources: loads every source file in a folder.

"""

from __future__ import annotations

import dataclasses
import pathlib
from typing import Any

from . import markdown, settings


@dataclasses.dataclass
class Source:
    """The front matter and sections of a source file.

    Args:
        name: the name of the source file in lower case with words joined by
            underscores (without the '.md' extension).
        sections: `dict` with keys that are section names ('text', 'slides',
            or 'notes') and values that are the markdown of those sections.
            Defaults to an empty `dict`.
        metadata: the front matter of the source file. Defaults to an empty
            `dict`.
        path: the path to the source file, if it was loaded from a file.
            Defaults to `None`.

    """

    name: str
    sections: dict[str, str] = dataclasses.field(default_factory = dict)
    metadata: dict[str, Any] = dataclasses.field(default_factory = dict)
    path: pathlib.Path | None = None

    """ Class Methods """

    @classmethod
    def from_file(
            cls,
            path: str | pathlib.Path,
            name: str | None = None) -> Source:
        """Creates a source from a markdown file.

        Args:
            path: path to the markdown file.
            name: the name of the source. Defaults to `None`, which uses the
                normalized name of the file (see `markdown.normalize_name`).

        Returns:
            A source with the front matter and sections of the file.

        Raises:
            ValueError: if the front matter or a divider is not valid.

        """
        path = pathlib.Path(path)
        text = path.read_text(encoding = 'utf-8')
        try:
            return cls.from_text(
                text,
                name = name or markdown.normalize_name(path.stem),
                path = path)
        except ValueError as error:
            message = f'{path.name}: {error}'
            raise ValueError(message) from error

    @classmethod
    def from_text(
            cls,
            text: str,
            name: str,
            path: pathlib.Path | None = None) -> Source:
        """Creates a source from markdown text.

        Args:
            text: the contents of a source file.
            name: the name of the source.
            path: the path to the source file, if any. Defaults to `None`.

        Returns:
            A source with the front matter and sections of `text`.

        """
        metadata, body = markdown.split_front_matter(text)
        sections = markdown.split_sections(
            body,
            names = settings.SECTION_ALIASES,
            default = 'text')
        return cls(
            name = name,
            sections = sections,
            metadata = metadata,
            path = path)

    """ Public Methods """

    def get(self, section: str) -> str:
        """Returns the markdown of `section`.

        Args:
            section: 'text', 'slides', or 'notes'.

        Returns:
            The markdown of the section, or an empty `str` if the source does
                not have that section.

        """
        return self.sections.get(section, '')


""" Public Functions """


def load_sources(folder: str | pathlib.Path) -> dict[str, Source]:
    """Loads every markdown file in `folder`.

    Subfolders are not searched.

    Args:
        folder: the project folder.

    Returns:
        A `dict` with keys that are the names of the sources (see
            `markdown.normalize_name`) and values that are the sources.

    Raises:
        ValueError: if two files have the same normalized name (such as
            'Introduction.md' and 'introduction.md') or a file is not valid.

    """
    sources: dict[str, Source] = {}
    for path in sorted(pathlib.Path(folder).glob('*.md')):
        source = Source.from_file(path)
        if source.name in sources:
            other = sources[source.name].path
            name = other.name if other else source.name
            message = f'{path.name} and {name} are for the same outline entry'
            raise ValueError(message)
        sources[source.name] = source
    return sources
