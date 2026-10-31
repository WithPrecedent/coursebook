"""Exports assembled markdown to Word, PowerPoint, PDF, and HTML files.

The "Text Format", "Slides Format", and "Notes Format" settings of a project
choose exporters by name. Every subclass of `Exporter` is registered
automatically, so other formats can be added by subclassing `Exporter`.

PDF files are made with [Typst](https://typst.app/) instead of LaTeX, so they
only need the `typst` package (installed with `pip install "coursebook[pdf]"`).

Contents:
    ExportOptions: options shared by every exporter.
    Exporter: base class for exporters.
    HtmlExporter: exports a document to a single HTML file.
    PdfExporter: exports a document to a PDF file.
    PowerPointExporter: exports a slide deck to a PowerPoint file.
    WordExporter: exports a document to a Word file.
    get_exporter: returns the exporter with a name.

"""

from __future__ import annotations

import dataclasses
import os
import pathlib
import tempfile
from typing import TYPE_CHECKING, Any, ClassVar

import pypandoc
import wonka
import yaml

from . import markdown

if TYPE_CHECKING:
    from collections.abc import Sequence

    from . import styles


@dataclasses.dataclass
class ExportOptions:
    """Options shared by every exporter.

    Args:
        template: path to the reference document that pandoc copies styles
            from. Defaults to `None`, which uses pandoc's default.
        metadata: document metadata (such as 'title' and 'author') that pandoc
            uses for the title page or title slide. Defaults to an empty
            `dict`.
        resource_paths: folders that pandoc searches for images. Defaults to
            an empty `list`.
        bibliography: paths to bibliography files. If any are given, pandoc
            formats citations (such as '[@smith2020]'). Defaults to an empty
            `list`.
        csl: path to a Citation Style Language file. Defaults to `None`.
        table_of_contents: whether to add a table of contents. Defaults to
            `False`.
        formatting: the formatting of the style, which PDF and HTML exporters
            pass to pandoc's templates. Defaults to `None`.

    """

    template: pathlib.Path | None = None
    metadata: dict[str, Any] = dataclasses.field(default_factory = dict)
    resource_paths: list[pathlib.Path] = dataclasses.field(
        default_factory = list)
    bibliography: list[pathlib.Path] = dataclasses.field(
        default_factory = list)
    csl: pathlib.Path | None = None
    table_of_contents: bool = False
    formatting: styles.Formatting | None = None


@dataclasses.dataclass
class Exporter(wonka.AutoRegistrar):
    """Base class for exporters.

    Attributes:
        aliases: names (in lower case with underscores) that choose this
            exporter in a project file.
        application: the application whose templates the exporter uses
            ('word' or 'powerpoint'), or an empty `str` if it uses none.
        extension: the file extension of exported files, without a period.
        pandoc_format: the name of the output format in pandoc.
        registry: every `Exporter` subclass, with keys that are the snake case
            names of the classes.
        sections: the sections that the exporter can export.

    """

    aliases: ClassVar[tuple[str, ...]] = ()
    application: ClassVar[str] = ''
    extension: ClassVar[str] = ''
    pandoc_format: ClassVar[str] = ''
    sections: ClassVar[tuple[str, ...]] = ('text', 'notes')

    """ Public Methods """

    def export(
            self,
            text: str,
            path: pathlib.Path,
            options: ExportOptions | None = None) -> pathlib.Path:
        """Exports markdown `text` to the file at `path`.

        Args:
            text: pandoc markdown.
            path: path for the exported file.
            options: export options. Defaults to `None`, which uses the
                defaults of `ExportOptions`.

        Returns:
            The path to the exported file.

        """
        options = options or ExportOptions()
        text = _add_metadata(text, self.get_metadata(options))
        pypandoc.convert_text(
            text,
            to = self.pandoc_format,
            format = 'markdown',
            outputfile = str(path),
            extra_args = self.get_arguments(options))
        return path

    def get_arguments(self, options: ExportOptions) -> list[str]:
        """Returns the pandoc command line arguments for `options`.

        Args:
            options: export options.

        Returns:
            The arguments to pass to pandoc.

        """
        arguments: list[str] = []
        if options.template is not None:
            arguments.append(f'--reference-doc={options.template}')
        if options.resource_paths:
            folders = _list_paths(options.resource_paths)
            arguments.append(f'--resource-path={folders}')
        if options.bibliography:
            arguments.append('--citeproc')
            arguments.extend(
                f'--bibliography={path}' for path in options.bibliography)
            if options.csl is not None:
                arguments.append(f'--csl={options.csl}')
        return arguments

    def get_metadata(self, options: ExportOptions) -> dict[str, Any]:
        """Returns the metadata to add to the start of the document.

        Args:
            options: export options.

        Returns:
            The metadata in `options`.

        """
        return dict(options.metadata)


@dataclasses.dataclass
class PowerPointExporter(Exporter):
    """Exports a slide deck to a PowerPoint file.

    Attributes:
        slide_level: the heading level that starts a new slide. Headings above
            it become section title slides.

    """

    aliases: ClassVar[tuple[str, ...]] = ('powerpoint', 'pptx')
    application: ClassVar[str] = 'powerpoint'
    extension: ClassVar[str] = 'pptx'
    pandoc_format: ClassVar[str] = 'pptx'
    sections: ClassVar[tuple[str, ...]] = ('slides',)
    slide_level: ClassVar[int] = 2

    """ Public Methods """

    def get_arguments(self, options: ExportOptions) -> list[str]:
        """Returns the pandoc command line arguments for `options`.

        Args:
            options: export options. `table_of_contents` is ignored.

        Returns:
            The arguments to pass to pandoc.

        """
        arguments = super().get_arguments(options)
        arguments.append(f'--slide-level={self.slide_level}')
        return arguments


@dataclasses.dataclass
class WordExporter(Exporter):
    """Exports a document to a Word file.

    Attributes:
        toc_depth: the deepest heading level in the table of contents.

    """

    aliases: ClassVar[tuple[str, ...]] = ('word', 'docx')
    application: ClassVar[str] = 'word'
    extension: ClassVar[str] = 'docx'
    pandoc_format: ClassVar[str] = 'docx'
    toc_depth: ClassVar[int] = 3

    """ Public Methods """

    def get_arguments(self, options: ExportOptions) -> list[str]:
        """Returns the pandoc command line arguments for `options`.

        Args:
            options: export options.

        Returns:
            The arguments to pass to pandoc.

        """
        arguments = super().get_arguments(options)
        if options.table_of_contents:
            arguments.extend(['--toc', f'--toc-depth={self.toc_depth}'])
        return arguments


@dataclasses.dataclass
class HtmlExporter(Exporter):
    """Exports a document to a single HTML file.

    Images and styles are included in the file, so it can be shared or posted
    on its own.

    Attributes:
        toc_depth: the deepest heading level in the table of contents.

    """

    aliases: ClassVar[tuple[str, ...]] = ('html', 'web')
    extension: ClassVar[str] = 'html'
    pandoc_format: ClassVar[str] = 'html5'
    toc_depth: ClassVar[int] = 3

    """ Public Methods """

    def get_arguments(self, options: ExportOptions) -> list[str]:
        """Returns the pandoc command line arguments for `options`.

        Math is written as MathML so that pandoc does not need to download a
        math script to include in the file.

        Args:
            options: export options. `template` is ignored.

        Returns:
            The arguments to pass to pandoc.

        """
        options = dataclasses.replace(options, template = None)
        arguments = super().get_arguments(options)
        arguments.extend(['--standalone', '--embed-resources', '--mathml'])
        if options.table_of_contents:
            arguments.extend(['--toc', f'--toc-depth={self.toc_depth}'])
        return arguments

    def get_metadata(self, options: ExportOptions) -> dict[str, Any]:
        """Returns the metadata, with the formatting for pandoc's template.

        Args:
            options: export options.

        Returns:
            The metadata in `options` and the template variables and styles
                for `options.formatting`.

        """
        metadata = super().get_metadata(options)
        formatting = options.formatting
        if formatting is None:
            return metadata
        if formatting.body_font:
            # Pandoc reads metadata as markdown and would curl quotation marks,
            # so the font name is not quoted (which CSS allows).
            metadata['mainfont'] = f'{formatting.body_font}, serif'
        if formatting.font_size:
            metadata['fontsize'] = f'{formatting.font_size}pt'
        if formatting.line_spacing:
            metadata['linestretch'] = formatting.line_spacing
        rules = []
        if formatting.heading_font:
            rules.append(
                f'h1, h2, h3, h4, h5, h6 {{ font-family: '
                f'"{formatting.heading_font}", serif; }}')
        if formatting.heading_color:
            rules.append(
                f'h1, h2, h3, h4, h5, h6, .title {{ color: '
                f'#{formatting.heading_color}; }}')
        if formatting.first_line_indent:
            rules.append(
                f'p + p {{ text-indent: {formatting.first_line_indent}in; }}')
        if formatting.center_top_headings:
            rules.append('h1 { text-align: center; }')
        if formatting.capitalize_top_headings:
            rules.append('h1 { text-transform: uppercase; }')
        if rules:
            styles = '\n'.join(rules)
            metadata['header-includes'] = (
                f'```{{=html}}\n<style>\n{styles}\n</style>\n```\n')
        return metadata


@dataclasses.dataclass
class PdfExporter(Exporter):
    """Exports a document to a PDF file with Typst.

    Pandoc converts the document to Typst, and the `typst` package turns that
    into a PDF file. Fonts must be installed on the computer; Typst uses its
    own fonts in place of missing ones.

    Attributes:
        paper_size: the Typst name of the paper size.
        toc_depth: the deepest heading level in the table of contents.

    """

    aliases: ClassVar[tuple[str, ...]] = ('pdf',)
    extension: ClassVar[str] = 'pdf'
    pandoc_format: ClassVar[str] = 'typst'
    paper_size: ClassVar[str] = 'us-letter'
    toc_depth: ClassVar[int] = 3

    """ Public Methods """

    def export(
            self,
            text: str,
            path: pathlib.Path,
            options: ExportOptions | None = None) -> pathlib.Path:
        """Exports markdown `text` to the PDF file at `path`.

        Args:
            text: pandoc markdown.
            path: path for the exported file.
            options: export options. Defaults to `None`, which uses the
                defaults of `ExportOptions`.

        Returns:
            The path to the exported file.

        Raises:
            ImportError: if the `typst` package is not installed.

        """
        try:
            import typst  # noqa: PLC0415
        except ImportError as error:
            message = (
                'PDF export needs the "typst" package (install it with '
                'pip install "coursebook[pdf]")')
            raise ImportError(message) from error
        options = options or ExportOptions()
        with tempfile.TemporaryDirectory() as temporary:
            folder = pathlib.Path(temporary)
            source = folder / 'document.typ'
            # Pandoc runs in the temporary folder so that the images it copies
            # there have paths that Typst can find.
            pypandoc.convert_text(
                _add_metadata(text, self.get_metadata(options)),
                to = self.pandoc_format,
                format = 'markdown',
                outputfile = str(source),
                extra_args = self.get_arguments(options),
                cworkdir = temporary)
            typst.compile(str(source), output = str(path), root = temporary)
        return path

    def get_arguments(self, options: ExportOptions) -> list[str]:
        """Returns the pandoc command line arguments for `options`.

        Args:
            options: export options. `template` is ignored.

        Returns:
            The arguments to pass to pandoc.

        """
        options = dataclasses.replace(options, template = None)
        arguments = super().get_arguments(options)
        arguments.extend(['--standalone', '--extract-media=media'])
        if options.table_of_contents:
            arguments.extend(['--toc', f'--toc-depth={self.toc_depth}'])
        return arguments

    def get_metadata(self, options: ExportOptions) -> dict[str, Any]:
        """Returns the metadata, with the formatting for pandoc's template.

        Args:
            options: export options.

        Returns:
            The metadata in `options` and the template variables and Typst
                rules for `options.formatting`.

        """
        metadata = super().get_metadata(options)
        metadata['papersize'] = self.paper_size
        formatting = options.formatting
        if formatting is None:
            return metadata
        if formatting.body_font:
            metadata['mainfont'] = formatting.body_font
        if formatting.font_size:
            metadata['fontsize'] = f'{formatting.font_size}pt'
        if formatting.line_spacing:
            metadata['linestretch'] = formatting.line_spacing
        if formatting.margins is not None:
            margin = f'{formatting.margins}in'
            metadata['margin'] = {'x': margin, 'y': margin}
        if formatting.page_numbers:
            metadata['page-numbering'] = '1'
        rules = []
        if formatting.heading_font:
            rules.append(
                f'#show heading: set text(font: "{formatting.heading_font}")')
        if formatting.heading_color:
            rules.append(
                f'#show heading: set text(fill: '
                f'rgb("#{formatting.heading_color}"))')
        if formatting.first_line_indent:
            rules.append(
                f'#set par(first-line-indent: '
                f'{formatting.first_line_indent}in)')
        if formatting.footnote_size:
            rules.append(
                f'#show footnote.entry: set text(size: '
                f'{formatting.footnote_size}pt)')
        if formatting.center_top_headings:
            rules.append('#show heading.where(level: 1): set align(center)')
        if formatting.capitalize_top_headings:
            rules.append('#show heading.where(level: 1): upper')
        if rules:
            typst_rules = '\n'.join(rules)
            metadata['header-includes'] = (
                f'```{{=typst}}\n{typst_rules}\n```\n')
        return metadata


""" Public Functions """


def get_exporter(name: str) -> Exporter:
    """Returns the exporter with `name`.

    Args:
        name: the name of an `Exporter` subclass or one of its aliases (such as
            'word' or 'PowerPoint').

    Returns:
        An instance of the exporter.

    Raises:
        ValueError: if no exporter has `name`.

    """
    key = markdown.normalize_name(name)
    choices: dict[str, type[Exporter]] = {}
    for registered_name, registered in Exporter.registry.items():
        choices[str(registered_name)] = registered
        for alias in registered.aliases:
            choices.setdefault(alias, registered)
    choices.pop('exporter', None)
    if key not in choices:
        known = ', '.join(sorted(
            alias for exporter in choices.values()
            for alias in exporter.aliases))
        message = f'unknown format "{name}" (use one of: {known})'
        raise ValueError(message)
    return choices[key]()


""" Private Functions """


def _add_metadata(text: str, metadata: dict[str, Any]) -> str:
    """Adds a YAML metadata block with `metadata` to the start of `text`.

    A metadata block is used instead of pandoc's '--metadata' argument because
    pandoc reads values of that argument as YAML (so a title of 'No' would
    become `False`).

    Args:
        text: pandoc markdown.
        metadata: the metadata to add. Items with empty values are left out.

    Returns:
        `text` with the metadata block, or `text` unchanged if there is no
            metadata.

    """
    values = {key: value for key, value in metadata.items() if value}
    if not values:
        return text
    block = yaml.dump(
        values,
        Dumper = _MetadataDumper,
        allow_unicode = True,
        sort_keys = False)
    return f'---\n{block}---\n\n{text}'


def _list_paths(paths: Sequence[pathlib.Path]) -> str:
    """Returns `paths` as a single search path.

    Args:
        paths: folders to search.

    Returns:
        The folders separated by the operating system's path separator.

    """
    return os.pathsep.join(str(path) for path in paths)


class _MetadataDumper(yaml.SafeDumper):
    """YAML dumper that writes multi-line strings as literal blocks.

    Pandoc reads metadata strings as markdown. A raw block (such as Typst
    rules in 'header-includes') is only recognized if its lines and final
    newline are kept, so multi-line strings are written in the literal ('|')
    style.

    """


def _represent_string(dumper: yaml.SafeDumper, value: str) -> yaml.Node:
    """Represents `value` as a literal block if it has more than one line.

    Args:
        dumper: the YAML dumper.
        value: the string to represent.

    Returns:
        The YAML node for `value`.

    """
    style = '|' if '\n' in value else None
    return dumper.represent_scalar(
        'tag:yaml.org,2002:str', value, style = style)


_MetadataDumper.add_representer(str, _represent_string)
