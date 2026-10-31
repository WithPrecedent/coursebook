"""The main interface for a `coursebook` project.

Contents:
    Project: the settings, outline, sources, and style of a project.
    build: builds the files of the project in a folder.
    _LOGGER: logger for warnings about missing source files.
    _PathLike: type of a path that may be a `str`.
    _SUFFIXES: the text added to the name of the file for each section.

"""

from __future__ import annotations

import concurrent.futures
import dataclasses
import logging
import pathlib
import tempfile
from typing import TYPE_CHECKING, TypeAlias

from . import (
    assembly,
    exporters,
    markdown,
    outline,
    settings,
    sources,
    styles,
    templates,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    # The classes are imported because the `outline` and `sources` fields of
    # `Project` hide the modules of the same names in its annotations.
    from .outline import OutlineEntry
    from .sources import Source

_LOGGER = logging.getLogger(__name__)
_PathLike: TypeAlias = str | pathlib.Path
_SUFFIXES: dict[str, str] = {'text': '', 'slides': '_slides', 'notes': '_notes'}


@dataclasses.dataclass
class Project:
    """The settings, outline, sources, and style of a project.

    Args:
        folder: the project folder, which holds the project file and the
            source files.
        settings: the settings in the project file.
        outline: the outline in the project file.
        sources: the source files, with keys that are their names (see
            `markdown.normalize_name`).
        style: the style that formats the project.

    """

    folder: pathlib.Path
    settings: settings.Settings
    outline: outline.Outline
    sources: dict[str, sources.Source]
    style: styles.Style

    """ Class Methods """

    @classmethod
    def from_folder(cls, folder: str | pathlib.Path = '.') -> Project:
        """Creates a project from the files in `folder`.

        Args:
            folder: the project folder. Defaults to the current folder.

        Returns:
            The project in `folder`.

        Raises:
            FileNotFoundError: if `folder` has no project file.
            ValueError: if the project file, a source file, or a setting is
                not valid.

        """
        folder = pathlib.Path(folder).resolve()
        path = settings.find_project_file(folder)
        project_settings, project_outline = settings.read_project_file(path)
        if not len(project_outline):
            message = f'{path.name} has no outline entries'
            raise ValueError(message)
        style = styles.get_style(
            project_settings.style,
            number_headings = project_settings.number_headings,
            table_of_contents = project_settings.table_of_contents)
        project_sources = sources.load_sources(folder)
        _load_named_sources(folder, project_outline, project_sources)
        _warn_shared_sources(project_outline)
        return cls(
            folder = folder,
            settings = project_settings,
            outline = project_outline,
            sources = project_sources,
            style = style)

    """ Properties """

    @property
    def include(self) -> list[str]:
        """Returns the sections to create files for.

        Returns:
            The "Include" setting, or the sections of the style if it is not
                set.

        """
        if self.settings.include is not None:
            return list(self.settings.include)
        return list(self.style.sections)

    @property
    def missing(self) -> list[OutlineEntry]:
        """Returns the outline entries that have no source file.

        Returns:
            The entries without a source file, in outline order.

        """
        return [
            entry for entry in self.outline
            if entry.name not in self.sources]

    @property
    def output_folder(self) -> pathlib.Path:
        """Returns the folder for the created files.

        Returns:
            The "Output Folder" setting, inside the project folder if it is a
                relative path.

        """
        return self._resolve(self.settings.output_folder)

    @property
    def unused(self) -> list[Source]:
        """Returns the source files that are not in the outline.

        Returns:
            The sources that no outline entry uses.

        """
        names = {entry.name for entry in self.outline}
        return [
            source for name, source in self.sources.items()
            if name not in names]

    """ Public Methods """

    def assemble(self, section: str) -> str:
        """Returns the combined markdown for `section`.

        Args:
            section: 'text', 'slides', or 'notes'.

        Returns:
            The markdown that is exported for `section`.

        Raises:
            ValueError: if `section` is not a known section.

        """
        if section == 'slides':
            return assembly.assemble_slides(
                self.outline,
                self.sources,
                style = self.style,
                section_slides = self.settings.section_slides)
        if section in settings.SECTIONS:
            return assembly.assemble_document(
                self.outline,
                self.sources,
                section = section,
                style = self.style,
                include_empty = section == 'text',
                visuals_in_notes = self.settings.visuals_in_notes)
        message = f'unknown section "{section}"'
        raise ValueError(message)

    def build(
            self,
            include: Iterable[str] | None = None,
            output_folder: _PathLike | None = None) -> list[pathlib.Path]:
        """Creates the files for the sections of the project.

        Each section is exported to every format set for it (such as Word and
        PDF). The files are exported at the same time, each in its own pandoc
        process.

        Args:
            include: the sections to create files for. Defaults to `None`,
                which uses `include`.
            output_folder: folder for the created files. Defaults to `None`,
                which uses `output_folder`.

        Returns:
            The paths to the created files, in the order of `include` and then
                of the formats of each section.

        Raises:
            FileNotFoundError: if a template, bibliography, or CSL file is not
                found.
            ImportError: if a format needs a package that is not installed.
            ValueError: if a section, format, or template is not valid, or a
                format cannot hold a section.
            RuntimeError: if pandoc fails.

        """
        sections = settings.normalize_sections(
            self.include if include is None else include)
        folder = (
            self.output_folder if output_folder is None
            else self._resolve(output_folder))
        for entry in self.missing:
            _LOGGER.warning(
                'No source file "%s" for outline entry "%s"',
                entry.file_name, entry.title)
        folder.mkdir(parents = True, exist_ok = True)
        stem = markdown.normalize_name(self.settings.name) or 'coursebook'
        with tempfile.TemporaryDirectory() as temporary:
            jobs = []
            for section in sections:
                text = self.assemble(section)
                for name in self.settings.formats_for(section):
                    exporter = exporters.get_exporter(name)
                    if section not in exporter.sections:
                        message = (
                            f'the {section} cannot be exported to {name} '
                            f'(use {", ".join(_formats_for(section))})')
                        raise ValueError(message)
                    options = self._get_options(
                        section, exporter, pathlib.Path(temporary))
                    path = folder / (
                        f'{stem}{_SUFFIXES[section]}.{exporter.extension}')
                    jobs.append((exporter, text, path, options))
            with concurrent.futures.ThreadPoolExecutor() as pool:
                futures = [pool.submit(job[0].export, *job[1:]) for job in jobs]
                return [future.result() for future in futures]

    """ Private Methods """

    def _get_options(
            self,
            section: str,
            exporter: exporters.Exporter,
            temporary: pathlib.Path) -> exporters.ExportOptions:
        """Returns the export options for `section`.

        Args:
            section: 'text', 'slides', or 'notes'.
            exporter: the exporter for `section`.
            temporary: folder for converted and created templates.

        Returns:
            The export options.

        Raises:
            FileNotFoundError: if the template, a bibliography file, or the CSL
                file is not found.

        """
        bibliography = [self._find(path) for path in self.settings.bibliography]
        # The citation style only matters when there are citations to format.
        csl_name = self.settings.csl or self.style.csl
        csl = None
        if bibliography and csl_name:
            csl = templates.find_template(
                csl_name, application = 'csl', folder = self.folder)
        metadata = {
            'title': self.settings.name,
            'subtitle': self.settings.subtitle,
            'author': self.settings.author,
            'date': self.settings.date}
        if section == 'notes':
            subtitle = self.settings.subtitle
            metadata['subtitle'] = f'{subtitle}: Notes' if subtitle else 'Notes'
        return exporters.ExportOptions(
            template = self._get_template(section, exporter, temporary),
            metadata = metadata,
            resource_paths = [
                self.folder, self._resolve(self.settings.visuals_folder)],
            bibliography = bibliography,
            csl = csl,
            table_of_contents = self.style.table_of_contents,
            formatting = self.style.formatting)

    def _get_template(
            self,
            section: str,
            exporter: exporters.Exporter,
            temporary: pathlib.Path) -> pathlib.Path | None:
        """Returns the reference document for `section`.

        Args:
            section: 'text', 'slides', or 'notes'.
            exporter: the exporter for `section`.
            temporary: folder for converted and created templates.

        Returns:
            The path to the reference document, or `None` to use pandoc's
                default or if the exporter does not use one.

        """
        if exporter.application not in {'word', 'powerpoint'}:
            return None
        name = self.settings.template_for(section)
        if name is None:
            if exporter.application == 'word':
                name = self.style.text_template
            elif exporter.application == 'powerpoint':
                name = self.style.slides_template
        if name is None:
            if exporter.application != 'word':
                return None
            path = temporary / f'{section}_reference.docx'
            return templates.create_word_template(self.style.formatting, path)
        found = templates.find_template(
            name, application = exporter.application, folder = self.folder)
        return templates.prepare_template(found, temporary / section)

    def _find(self, name: str) -> pathlib.Path:
        """Returns the path to a file named in the settings.

        Args:
            name: a path, absolute or relative to the project folder.

        Returns:
            The path to the file.

        Raises:
            FileNotFoundError: if the file does not exist.

        """
        path = self._resolve(name)
        if not path.is_file():
            message = f'file {name} not found in {self.folder}'
            raise FileNotFoundError(message)
        return path

    def _resolve(self, name: str | pathlib.Path) -> pathlib.Path:
        """Returns a path, placing a relative path inside the project folder.

        Args:
            name: an absolute path or a path relative to the project folder.

        Returns:
            The absolute path.

        """
        return self.folder / pathlib.Path(name).expanduser()


""" Public Functions """


def build(
        folder: str | pathlib.Path = '.',
        include: Iterable[str] | None = None,
        output_folder: _PathLike | None = None) -> list[pathlib.Path]:
    """Builds the files of the project in `folder`.

    Args:
        folder: the project folder. Defaults to the current folder.
        include: the sections to create files for. Defaults to `None`, which
            uses the "Include" setting or the sections of the style.
        output_folder: folder for the created files. Defaults to `None`,
            which uses the "Output Folder" setting.

    Returns:
        The paths to the created files.

    """
    project = Project.from_folder(folder)
    return project.build(include = include, output_folder = output_folder)


""" Private Functions """


def _formats_for(section: str) -> list[str]:
    """Returns the names of the formats that can hold `section`.

    Args:
        section: 'text', 'slides', or 'notes'.

    Returns:
        The first alias of each exporter that can export `section`.

    """
    return sorted({
        exporter.aliases[0] for exporter in exporters.Exporter.registry.values()
        if exporter.aliases and section in exporter.sections})


def _load_named_sources(
        folder: pathlib.Path,
        project_outline: outline.Outline,
        project_sources: dict[str, sources.Source]) -> None:
    """Loads the source files that the outline names (with '| file.md').

    Files in the project folder are already loaded, so this loads the files in
    subfolders and adds them to `project_sources`.

    Args:
        folder: the project folder.
        project_outline: the outline of the project.
        project_sources: the loaded sources, which are changed in place.

    Raises:
        ValueError: if a named file is not valid.

    """
    for entry in project_outline:
        if entry.file is None or entry.name in project_sources:
            continue
        path = folder / entry.file
        if path.is_file():
            project_sources[entry.name] = sources.Source.from_file(
                path, name = entry.name)


def _warn_shared_sources(project_outline: outline.Outline) -> None:
    """Warns when outline entries would use the same source file.

    Args:
        project_outline: the outline of the project.

    """
    seen: dict[str, outline.OutlineEntry] = {}
    for entry in project_outline:
        if entry.name in seen:
            _LOGGER.warning(
                'Outline entries "%s" and "%s" both use "%s" (add '
                '"| other_file.md" to one of them to give it its own file)',
                seen[entry.name].title, entry.title, entry.file_name)
        else:
            seen[entry.name] = entry
