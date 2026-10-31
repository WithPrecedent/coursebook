"""Loads the settings and outline of a `coursebook` project.

A project file is named 'project' with an 'ini', 'toml', 'yaml', or 'yml'
extension. It has a "Project" section with settings and an "Outline" section
with the structure of the project.

The outline of an `ini` file is read line by line instead of with
`configparser` because outlines repeat labels (such as an 'A' under 'I' and
another 'A' under 'II'), which `configparser` does not allow. For the same
reason, the outline in a `toml` or `yaml` file is a list instead of a table.

Contents:
    OutlineLines: type of the outline lines read from a project file.
    PROJECT_FILE_NAMES: the names that a project file may have.
    SECTION_ALIASES: other names that may be used for each section.
    SECTIONS: the kinds of sections that a source file may have.
    Settings: the options in the "Project" section of a project file.
    find_project_file: returns the path to the project file in a folder.
    normalize_sections: converts section names to their standard names.
    read_project_file: returns the settings and outline in a project file.
    _INI_SECTION: matches a section header in an `ini` file.
    _LIST_SEPARATORS: the separators used to split `ini` values into lists.
    _SETTING_ALIASES: other names that may be used for some settings.

"""

from __future__ import annotations

import configparser
import dataclasses
import pathlib
import re
import tomllib
from typing import TYPE_CHECKING, Any, TypeAlias

import camina
import yaml

from . import markdown, outline

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

OutlineLines: TypeAlias = list[outline.OutlineLine]
PROJECT_FILE_NAMES: tuple[str, ...] = (
    'project.ini', 'project.toml', 'project.yaml', 'project.yml')
SECTIONS: tuple[str, ...] = ('text', 'slides', 'notes')
SECTION_ALIASES: dict[str, str] = {
    'text': 'text',
    'manuscript': 'text',
    'slides': 'slides',
    'notes': 'notes'}
# Authors are split on semicolons because names may include commas (such as
# 'Martin Luther King, Jr.').
_LIST_SEPARATORS: dict[str, str] = {
    'author': r'[;\n]'}
_SETTING_ALIASES: dict[str, str] = {
    'authors': 'author',
    'notes_formats': 'notes_format',
    'project_name': 'name',
    'slide_template': 'slides_template',
    'slides_formats': 'slides_format',
    'text_formats': 'text_format',
    'title': 'name',
    'toc': 'table_of_contents'}
_INI_SECTION: re.Pattern[str] = re.compile(r'^\s*\[([^\]]+)\]\s*$')


@dataclasses.dataclass
class Settings:
    """The options in the "Project" section of a project file.

    Names in a project file are matched without regard to case, spaces, or
    underscores. So, 'Output Folder' sets `output_folder`.

    Args:
        name: the title of the project. It is also used (in lower case with
            underscores) for the names of the created files. Defaults to
            'Untitled'.
        style: name of the `Style` that formats the project. Defaults to
            'coursebook'.
        include: the sections to create files for ('text', 'slides', and/or
            'notes'). Defaults to `None`, which uses the sections of the
            style.
        author: the authors of the project. Defaults to an empty `list`.
        subtitle: the subtitle of the project. Defaults to `None`.
        date: the date shown on the title page and title slide. Defaults to
            `None`.
        output_folder: folder for the created files. A relative path is placed
            inside the project folder. Defaults to 'output'.
        visuals_folder: folder with the images used in the source files. A
            relative path is placed inside the project folder. Defaults to
            'visuals'.
        text_template: name or path of the Word template for the text.
            Defaults to `None`, which uses the template of the style.
        slides_template: name or path of the PowerPoint template for the
            slides. Defaults to `None`, which uses the template of the style.
        notes_template: name or path of the Word template for the notes.
            Defaults to `None`, which uses `text_template`.
        text_format: the formats of the text files ('word', 'pdf', and/or
            'html'). Defaults to ['word'].
        slides_format: the formats of the slides files. Defaults to
            ['powerpoint'].
        notes_format: the formats of the notes files ('word', 'pdf', and/or
            'html'). Defaults to ['word'].
        bibliography: paths to bibliography files (such as BibTeX files) for
            citations. Defaults to an empty `list`.
        csl: name or path of a Citation Style Language file for formatting
            citations. A name is looked for in the project folder and then
            among the styles included with `coursebook` (such as
            'bluebook-law-review'). Defaults to `None`, which uses the style's
            CSL or, if it has none, pandoc's default (Chicago author-date).
        table_of_contents: whether to add a table of contents to the text and
            notes. Defaults to `None`, which uses the setting of the style.
        number_headings: whether to put the outline labels in headings (such
            as 'I. Introduction'). Defaults to `None`, which uses the setting
            of the style.
        section_slides: whether to add a slide with the title of each outline
            entry before its slides. Defaults to `True`.
        visuals_in_notes: whether to copy the images in the text of each
            source file into its notes. A source file can change this in its
            front matter. Defaults to `False`.
        extras: settings that `coursebook` does not use itself, such as those
            for a custom `Style`. Defaults to an empty `dict`.

    """

    name: str = 'Untitled'
    style: str = 'coursebook'
    include: list[str] | None = None
    author: list[str] = dataclasses.field(default_factory = list)
    subtitle: str | None = None
    date: str | None = None
    output_folder: str = 'output'
    visuals_folder: str = 'visuals'
    text_template: str | None = None
    slides_template: str | None = None
    notes_template: str | None = None
    text_format: list[str] = dataclasses.field(
        default_factory = lambda: ['word'])
    slides_format: list[str] = dataclasses.field(
        default_factory = lambda: ['powerpoint'])
    notes_format: list[str] = dataclasses.field(
        default_factory = lambda: ['word'])
    bibliography: list[str] = dataclasses.field(default_factory = list)
    csl: str | None = None
    table_of_contents: bool | None = None
    number_headings: bool | None = None
    section_slides: bool = True
    visuals_in_notes: bool = False
    extras: dict[str, Any] = dataclasses.field(default_factory = dict)

    """ Initialization Methods """

    def __post_init__(self) -> None:
        """Validates and normalizes the sections in `include`.

        Raises:
            ValueError: if `include` names an unknown section.

        """
        if self.include is not None:
            self.include = normalize_sections(self.include)

    """ Class Methods """

    @classmethod
    def from_mapping(
            cls,
            mapping: Mapping[str, Any],
            infer_types: bool = False) -> Settings:
        """Creates settings from a `dict` of options.

        Args:
            mapping: options with names as they appear in a project file (such
                as 'Output Folder').
            infer_types: whether to convert `str` values to other types (such
                as `bool` or `list`). This should be `True` for `ini` files,
                which only store `str` values. Defaults to `False`.

        Returns:
            Settings with the options in `mapping`.

        Raises:
            ValueError: if a setting has a value of the wrong type or
                `include` names an unknown section.

        """
        fields = {field.name: field for field in dataclasses.fields(cls)}
        kwargs: dict[str, Any] = {}
        extras: dict[str, Any] = {}
        for key, value in mapping.items():
            name = markdown.normalize_name(str(key))
            name = _SETTING_ALIASES.get(name, name)
            if name not in fields or name == 'extras':
                extras[name] = camina.typify(value) if infer_types else value
                continue
            kwargs[name] = _convert_setting(name, value, fields[name].type)
        return cls(**kwargs, extras = extras)

    """ Public Methods """

    def formats_for(self, section: str) -> list[str]:
        """Returns the formats of the files for `section`.

        Args:
            section: 'text', 'slides', or 'notes'.

        Returns:
            The names of the formats (such as ['word', 'pdf']).

        """
        return list(getattr(self, f'{section}_format'))

    def template_for(self, section: str) -> str | None:
        """Returns the template setting for `section`.

        Args:
            section: 'text', 'slides', or 'notes'.

        Returns:
            The name or path of the template, or `None` if the setting is not
                set. The notes use `text_template` if `notes_template` is not
                set.

        """
        template = getattr(self, f'{section}_template')
        if template is None and section == 'notes':
            template = self.text_template
        return None if template is None else str(template)


""" Public Functions """


def find_project_file(folder: str | pathlib.Path) -> pathlib.Path:
    """Returns the path to the project file in `folder`.

    Args:
        folder: the project folder.

    Returns:
        The path to the project file.

    Raises:
        FileNotFoundError: if `folder` does not exist or has no project file.
        ValueError: if `folder` has more than one project file.

    """
    folder = pathlib.Path(folder)
    if not folder.is_dir():
        message = f'project folder {folder} does not exist'
        raise FileNotFoundError(message)
    names = {path.name.lower(): path for path in folder.iterdir()}
    found = [names[name] for name in PROJECT_FILE_NAMES if name in names]
    if not found:
        message = (
            f'no project file in {folder} (expected one of: '
            f'{", ".join(PROJECT_FILE_NAMES)})')
        raise FileNotFoundError(message)
    if len(found) > 1:
        listed = ', '.join(path.name for path in found)
        message = f'{folder} has more than one project file ({listed})'
        raise ValueError(message)
    return found[0]


def normalize_sections(sections: Iterable[str]) -> list[str]:
    """Converts section names (and their aliases) to their standard names.

    Args:
        sections: section names (such as 'manuscript' or 'Slides').

    Returns:
        The standard names of the sections ('text', 'slides', or 'notes'),
            without duplicates.

    Raises:
        ValueError: if a name is not a known section.

    """
    normalized: list[str] = []
    for section in sections:
        name = SECTION_ALIASES.get(markdown.normalize_name(section))
        if name is None:
            known = ', '.join(SECTIONS)
            message = f'unknown section "{section}" (use {known})'
            raise ValueError(message)
        if name not in normalized:
            normalized.append(name)
    return normalized


def read_project_file(
        path: str | pathlib.Path) -> tuple[Settings, outline.Outline]:
    """Returns the settings and outline in a project file.

    Args:
        path: path to an `ini`, `toml`, `yaml`, or `yml` project file.

    Returns:
        The settings from the "Project" section and the outline from the
            "Outline" section.

    Raises:
        FileNotFoundError: if `path` is not a file.
        ValueError: if the file type is not supported or the contents are not
            valid.

    """
    path = pathlib.Path(path)
    if not path.is_file():
        message = f'project file {path} not found'
        raise FileNotFoundError(message)
    suffix = path.suffix.lower()
    if suffix == '.ini':
        options, lines = _read_ini(path)
        settings = Settings.from_mapping(options, infer_types = True)
    elif suffix in {'.toml', '.yaml', '.yml'}:
        options, lines = _read_structured(path)
        settings = Settings.from_mapping(options)
    else:
        message = f'{path.name} is not an ini, toml, or yaml file'
        raise ValueError(message)
    return settings, outline.Outline.from_lines(lines)


""" Private Functions """


def _convert_setting(name: str, value: Any, annotation: Any) -> Any:
    """Converts `value` to the type of the setting `name`.

    Args:
        name: the name of a `Settings` field.
        value: the value from a project file.
        annotation: the type annotation of the field (as a `str`, since
            annotations are postponed).

    Returns:
        The converted value.

    Raises:
        ValueError: if `value` cannot be converted.

    """
    annotation = str(annotation)
    if annotation.startswith('list'):
        if isinstance(value, str):
            separator = _LIST_SEPARATORS.get(name, r'[,\n]')
            return [
                item.strip() for item in re.split(separator, value)
                if item.strip()]
        if isinstance(value, list | tuple):
            return [str(item) for item in value]
        return [str(value)]
    if annotation.startswith('bool'):
        converted = camina.typify(value) if isinstance(value, str) else value
        if not isinstance(converted, bool):
            message = f'the "{name}" setting must be yes or no, not "{value}"'
            raise ValueError(message)
        return converted
    return str(value).strip()


def _outline_items(items: Any) -> OutlineLines:
    """Converts the outline in a `toml` or `yaml` file to outline lines.

    Args:
        items: a `list` whose items are lines (such as 'A: History'),
            lists of a label, a title, and (optionally) a file, or (in
            `yaml`) one-item mappings of a label to a title.

    Returns:
        The outline lines and tuples of their parts.

    Raises:
        ValueError: if `items` is not a `list` or has an item of another form.

    """
    if not isinstance(items, list):
        message = 'the outline must be a list (such as ["I: Introduction"])'
        raise ValueError(message)  # noqa: TRY004
    lines: OutlineLines = []
    for item in items:
        if isinstance(item, str):
            lines.append(item)
        elif isinstance(item, dict) and len(item) == 1:
            label, title = next(iter(item.items()))
            lines.append((str(label), str(title)))
        elif isinstance(item, list | tuple) and len(item) in {2, 3}:
            lines.append(tuple(str(part) for part in item))
        else:
            message = f'outline item {item!r} needs a label and a title'
            raise ValueError(message)
    return lines


def _read_ini(path: pathlib.Path) -> tuple[dict[str, Any], OutlineLines]:
    """Reads the project options and outline lines from an `ini` file.

    Args:
        path: path to an `ini` file.

    Returns:
        The options in the "Project" section and the lines in the "Outline"
            section.

    Raises:
        ValueError: if the file has no "Project" section or is not a valid
            `ini` file.

    """
    other: list[str] = []
    lines: OutlineLines = []
    in_outline = False
    for line in path.read_text(encoding = 'utf-8').splitlines():
        header = _INI_SECTION.match(line)
        if header:
            in_outline = markdown.normalize_name(header.group(1)) == 'outline'
            if in_outline:
                continue
        if in_outline:
            if not line.strip().startswith(('#', ';')):
                lines.append(line)
        else:
            other.append(line)
    parser = configparser.ConfigParser(interpolation = None)
    parser.optionxform = str  # type: ignore[assignment,method-assign]
    try:
        parser.read_string('\n'.join(other), source = str(path))
    except configparser.Error as error:
        message = f'{path.name} is not a valid ini file: {error}'
        raise ValueError(message) from error
    sections = {
        markdown.normalize_name(name): dict(parser[name])
        for name in parser.sections()}
    if 'project' not in sections:
        message = f'{path.name} has no [Project] section'
        raise ValueError(message)
    return sections['project'], lines


def _read_structured(
        path: pathlib.Path) -> tuple[dict[str, Any], OutlineLines]:
    """Reads the project options and outline from a `toml` or `yaml` file.

    The outline may be at the top level of the file or inside the "project"
    table.

    Args:
        path: path to a `toml`, `yaml`, or `yml` file.

    Returns:
        The options in the "project" table and the outline lines.

    Raises:
        ValueError: if the file has no "project" table or is not valid.

    """
    text = path.read_text(encoding = 'utf-8')
    try:
        if path.suffix.lower() == '.toml':
            data = tomllib.loads(text)
        else:
            data = yaml.safe_load(text) or {}
    except (tomllib.TOMLDecodeError, yaml.YAMLError) as error:
        message = f'{path.name} could not be read: {error}'
        raise ValueError(message) from error
    data = {
        markdown.normalize_name(str(key)): value
        for key, value in data.items()}
    if not isinstance(data.get('project'), dict):
        message = f'{path.name} has no "project" table'
        raise ValueError(message)  # noqa: TRY004
    options = {
        markdown.normalize_name(str(key)): value
        for key, value in data['project'].items()}
    items = data.get('outline', options.pop('outline', []))
    return options, _outline_items(items)
