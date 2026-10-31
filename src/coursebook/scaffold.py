"""Creates the files for new projects and editable templates.

Contents:
    PROJECT_FILE_FORMATS: the formats that a new project file may use.
    create_project: creates a project folder with a project file and source
        files.
    write_template: writes the Word or PowerPoint template of a style.
    _DEFAULT_OUTLINE: the outline used when none is given.

"""

from __future__ import annotations

import json
import pathlib
import shutil
import string
import tempfile
from typing import TYPE_CHECKING, Any

import yaml

from . import outline, settings, styles, templates

if TYPE_CHECKING:
    from collections.abc import Iterable

PROJECT_FILE_FORMATS: tuple[str, ...] = ('ini', 'toml', 'yaml')
_DEFAULT_OUTLINE: tuple[str, ...] = (
    'I: Introduction',
    'II: Background',
    'III: Analysis',
    'IV: Conclusion')


""" Public Functions """


def create_project(
        folder: str | pathlib.Path,
        name: str | None = None,
        style: str = 'coursebook',
        outline_lines: Iterable[outline.OutlineLine] | None = None,
        file_format: str = 'ini') -> list[pathlib.Path]:
    """Creates a project folder with a project file and source files.

    Each outline entry gets a source file with a divider for each section of
    the style. Source files that already exist are left alone. If two entries
    would share a source file (because they have the same title), the later
    one is given its own file in the outline.

    Args:
        folder: the project folder, which is created if it does not exist.
        name: the title of the project. Defaults to `None`, which uses the
            name of `folder` in title case, with spaces for underscores and
            dashes.
        style: the name of the style. Defaults to 'coursebook'.
        outline_lines: the outline of the project. Defaults to `None`, which
            uses a short sample outline.
        file_format: the format of the project file ('ini', 'toml', or
            'yaml'). Defaults to 'ini'.

    Returns:
        The paths to the files and folders that were created.

    Raises:
        FileExistsError: if `folder` already has a project file.
        ValueError: if the style, outline, or file format is not valid.

    """
    folder = pathlib.Path(folder)
    if file_format not in PROJECT_FILE_FORMATS:
        message = (
            f'unknown project file format "{file_format}" (use '
            f'{", ".join(PROJECT_FILE_FORMATS)})')
        raise ValueError(message)
    try:
        existing = settings.find_project_file(folder)
    except FileNotFoundError:
        pass
    else:
        message = f'{folder} already has a project file ({existing.name})'
        raise FileExistsError(message)
    project_style = styles.get_style(style)
    project_outline = outline.Outline.from_lines(
        list(outline_lines) if outline_lines else _DEFAULT_OUTLINE)
    _give_entries_own_files(project_outline)
    if not name:
        words = folder.resolve().name.replace('_', ' ').replace('-', ' ')
        name = string.capwords(words) or 'Untitled'
    folder.mkdir(parents = True, exist_ok = True)
    project_file = folder / f'project.{file_format}'
    project_file.write_text(
        _format_project_file(name, style, project_outline, file_format),
        encoding = 'utf-8')
    created = [project_file]
    skeleton = '\n\n\n'.join(
        f'<{section}>' for section in project_style.sections) + '\n'
    for entry in project_outline:
        path = folder / entry.file_name
        if path.exists():
            continue
        path.parent.mkdir(parents = True, exist_ok = True)
        path.write_text(skeleton, encoding = 'utf-8')
        created.append(path)
    visuals = folder / 'visuals'
    if not visuals.exists():
        visuals.mkdir()
        created.append(visuals)
    return created


def write_template(
        style: str,
        destination: str | pathlib.Path) -> pathlib.Path:
    """Writes the Word or PowerPoint template of a style.

    The template can be changed in Word or PowerPoint and then named in the
    "Text Template" or "Slides Template" setting of a project.

    Args:
        style: the name of the style.
        destination: path for the template. Its extension ('.docx' or
            '.pptx') chooses which template is written.

    Returns:
        The path to the template.

    Raises:
        FileExistsError: if `destination` already exists.
        ValueError: if the style or extension is not valid.

    """
    destination = pathlib.Path(destination)
    suffix = destination.suffix.lower()
    if suffix not in {'.docx', '.pptx'}:
        message = f'{destination.name} must end with .docx or .pptx'
        raise ValueError(message)
    if destination.exists():
        message = f'{destination} already exists'
        raise FileExistsError(message)
    project_style = styles.get_style(style)
    destination.parent.mkdir(parents = True, exist_ok = True)
    if suffix == '.docx':
        name = project_style.text_template
        if name is None:
            return templates.create_word_template(
                project_style.formatting, destination)
        application = 'word'
    else:
        name = project_style.slides_template
        if name is None:
            destination.write_bytes(templates.get_pandoc_template('pptx'))
            return destination
        application = 'powerpoint'
    found = templates.find_template(
        name, application = application, folder = pathlib.Path.cwd())
    with tempfile.TemporaryDirectory() as temporary:
        prepared = templates.prepare_template(found, temporary)
        shutil.copyfile(prepared, destination)
    return destination


""" Private Functions """


def _format_entry(entry: outline.OutlineEntry) -> str:
    """Returns the outline line for `entry`.

    Args:
        entry: an outline entry.

    Returns:
        The line, with dashes for an unnumbered entry and the file after a '|'
            if the entry names one.

    """
    label = entry.label or '-' * (entry.level + 1)
    line = f'{label}: {entry.title}'
    return f'{line} | {entry.file}' if entry.file else line


def _format_project_file(
        name: str,
        style: str,
        project_outline: outline.Outline,
        file_format: str) -> str:
    """Returns the contents of a new project file.

    Args:
        name: the title of the project.
        style: the name of the style.
        project_outline: the outline of the project.
        file_format: 'ini', 'toml', or 'yaml'.

    Returns:
        The text of the project file.

    """
    lines = [_format_entry(entry) for entry in project_outline]
    options: dict[str, Any] = {
        'name': name, 'style': style, 'output_folder': 'output'}
    if file_format == 'toml':
        items = ',\n'.join(f'    {json.dumps(line)}' for line in lines)
        values = '\n'.join(
            f'{key} = {json.dumps(value)}' for key, value in options.items())
        return f'outline = [\n{items}]\n\n[project]\n{values}\n'
    if file_format == 'yaml':
        return yaml.safe_dump(
            {'project': options, 'outline': lines},
            allow_unicode = True,
            sort_keys = False)
    outline_text = '\n'.join(lines)
    return (
        f'[Project]\nName: {name}\nStyle: {style}\n'
        '# Author: First Author; Second Author\n'
        '# Bibliography: references.bib\n'
        '# Text Format: word, pdf\n'
        f'Output Folder: output\n\n[Outline]\n{outline_text}\n')


def _give_entries_own_files(project_outline: outline.Outline) -> None:
    """Gives each outline entry that would share a source file its own file.

    Args:
        project_outline: the outline, whose entries are changed in place.

    """
    used: set[str] = set()
    for entry in project_outline:
        if entry.name in used:
            number = 2
            while f'{entry.name}_{number}' in used:
                number += 1
            entry.file = f'{entry.name}_{number}.md'
        used.add(entry.name)
