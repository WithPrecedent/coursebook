"""Command line interface for `coursebook`.

The commands are:

* `coursebook build [folder]` (or just `coursebook [folder]`): creates the
    files of a project.
* `coursebook new folder`: creates a new project.
* `coursebook template style destination`: writes the Word or PowerPoint
    template of a style so that it can be changed.

Contents:
    main: runs a command from the command line.
    _COMMANDS: the names of the commands.

"""

from __future__ import annotations

import argparse
import logging
import pathlib
import sys
from typing import TYPE_CHECKING

from . import __version__, project, scaffold, settings

if TYPE_CHECKING:
    from collections.abc import Sequence

_COMMANDS: tuple[str, ...] = ('build', 'new', 'template')


""" Public Functions """


def main(arguments: Sequence[str] | None = None) -> int:
    """Runs a command from the command line.

    If the first argument is not a command, the command is 'build'.

    Args:
        arguments: the command line arguments, without the program name.
            Defaults to `None`, which uses `sys.argv`.

    Returns:
        The exit status: 0 if the command succeeded and 1 otherwise.

    """
    values = list(sys.argv[1:] if arguments is None else arguments)
    if not values or values[0] not in {*_COMMANDS, '-h', '--help', '--version'}:
        values.insert(0, 'build')
    options = _create_parser().parse_args(values)
    logging.basicConfig(
        format = '%(levelname)s: %(message)s',
        level = (
            logging.INFO if getattr(options, 'verbose', False)
            else logging.WARNING))
    try:
        if options.command == 'new':
            paths = _new(options)
        elif options.command == 'template':
            paths = [scaffold.write_template(
                options.style, options.destination)]
        else:
            paths = _build(options)
    except (ImportError, OSError, RuntimeError, ValueError) as error:
        sys.stderr.write(f'coursebook: error: {error}\n')
        return 1
    for path in paths:
        sys.stdout.write(f'Created {path}\n')
    return 0


""" Private Functions """


def _build(options: argparse.Namespace) -> list[pathlib.Path]:
    """Builds a project from the parsed command line options.

    Args:
        options: the parsed options of the 'build' command.

    Returns:
        The paths to the created files.

    """
    project_ = project.Project.from_folder(options.folder)
    if options.verbose:
        for source in project_.unused:
            logging.info('Source file "%s" is not in the outline', (
                source.path.name if source.path else source.name))
    return project_.build(
        include = options.include,
        output_folder = options.output_folder)


def _create_parser() -> argparse.ArgumentParser:
    """Returns the parser for the command line arguments.

    Returns:
        The argument parser.

    """
    parser = argparse.ArgumentParser(
        prog = 'coursebook',
        description = (
            'Creates Word, PowerPoint, PDF, and HTML files from a project '
            'file and markdown source files.'))
    parser.add_argument(
        '--version',
        action = 'version',
        version = f'%(prog)s {__version__}')
    commands = parser.add_subparsers(dest = 'command', required = True)
    build = commands.add_parser(
        'build',
        help = 'create the files of a project (the default command)',
        description = 'Creates the files of a project.')
    build.add_argument(
        'folder',
        nargs = '?',
        default = '.',
        help = 'the project folder (defaults to the current folder)')
    build.add_argument(
        '-i', '--include',
        nargs = '+',
        metavar = 'SECTION',
        help = (
            'the sections to create files for, overriding the project file '
            f'(choices: {", ".join(settings.SECTIONS)})'))
    build.add_argument(
        '-o', '--output-folder',
        help = 'folder for the created files, overriding the project file')
    build.add_argument(
        '-v', '--verbose',
        action = 'store_true',
        help = 'report source files that are not in the outline')
    new = commands.add_parser(
        'new',
        help = 'create a new project',
        description = (
            'Creates a project folder with a project file, a source file for '
            'each outline entry, and a visuals folder.'))
    new.add_argument('folder', help = 'the folder for the new project')
    new.add_argument(
        '-n', '--name',
        help = 'the title of the project (defaults to the folder name)')
    new.add_argument(
        '-s', '--style',
        default = 'coursebook',
        help = 'the style of the project (defaults to coursebook)')
    new.add_argument(
        '-f', '--format',
        choices = scaffold.PROJECT_FILE_FORMATS,
        default = 'ini',
        help = 'the format of the project file (defaults to ini)')
    new.add_argument(
        '--outline',
        metavar = 'FILE',
        help = 'a text file with one outline line (such as "I: Introduction") '
               'per line')
    new.add_argument(
        '-e', '--entry',
        action = 'append',
        metavar = 'LINE',
        help = 'an outline line (repeat for each entry)')
    template = commands.add_parser(
        'template',
        help = "write a style's Word or PowerPoint template",
        description = (
            'Writes the Word (.docx) or PowerPoint (.pptx) template of a '
            'style so that it can be changed and named in a project file.'))
    template.add_argument('style', help = 'the name of the style')
    template.add_argument(
        'destination',
        help = 'the path for the template, ending in .docx or .pptx')
    return parser


def _new(options: argparse.Namespace) -> list[pathlib.Path]:
    """Creates a project from the parsed command line options.

    Args:
        options: the parsed options of the 'new' command.

    Returns:
        The paths to the created files and folders.

    """
    lines: list[str] = []
    if options.outline:
        text = pathlib.Path(options.outline).read_text(encoding = 'utf-8')
        lines.extend(
            line for line in text.splitlines()
            if line.strip() and not line.lstrip().startswith('#'))
    lines.extend(options.entry or [])
    return scaffold.create_project(
        options.folder,
        name = options.name,
        style = options.style,
        outline_lines = lines or None,
        file_format = options.format)
