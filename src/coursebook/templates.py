"""Finds and prepares the templates and citation styles used for exports.

Pandoc formats Word and PowerPoint files by copying the styles of a reference
document (a '.docx' or '.pptx' file). This module turns the templates that a
project names into reference documents:

* Word: '.docx' files are used as is and '.dotx' templates are converted. If
    a project does not name a Word template, pandoc's default template is used
    with the `Formatting` of the style applied.
* PowerPoint: '.pptx' files are used as is and '.potx' templates and '.thmx'
    Office themes are converted.

Citation Style Language ('.csl') files are found the same way as templates.

A template is found by its path (relative to the project folder) or by its
name. A name is looked for first in the project folder and then among the
templates included with `coursebook` (such as 'chalkboard' and
'bluebook-law-review').

Contents:
    create_word_template: creates a Word reference document with formatting.
    find_template: returns the path to a template.
    get_pandoc_template: returns pandoc's default reference document.
    list_templates: returns the names of the included templates.
    prepare_template: converts a template into a reference document.
    _DOCUMENT: the start of the Word content types.
    _EXTENSIONS: the template file extensions for each kind of template.
    _HEADING_STYLES: the Word styles that are formatted as headings.
    _MAIN_CONTENT_TYPES: the content types that templates are converted from
        and to.
    _PRESENTATION: the start of the PowerPoint content types.
    _PRESENTATION_NAMESPACES: the XML namespaces of PowerPoint parts.
    _RELATIONSHIPS: the namespace of Office relationship types.
    _TEMPLATES_FOLDER: folder with the templates included with `coursebook`.
    _THEME_EXTRA_PARTS: the parts that a presentation needs but an Office
        theme does not include.
    _XML_DECLARATION: the declaration at the start of each XML part.

"""

from __future__ import annotations

import pathlib
import re
import subprocess
import zipfile
from typing import TYPE_CHECKING

import docx
import pypandoc
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

if TYPE_CHECKING:
    from docx.document import Document
    from docx.oxml.xmlchemy import BaseOxmlElement
    from docx.section import Section
    from docx.styles.style import ParagraphStyle

    from . import styles

_TEMPLATES_FOLDER: pathlib.Path = pathlib.Path(__file__).parent / 'templates'
_EXTENSIONS: dict[str, tuple[str, ...]] = {
    'csl': ('.csl',),
    'powerpoint': ('.pptx', '.potx', '.thmx'),
    'word': ('.docx', '.dotx')}
_PRESENTATION: str = (
    'application/vnd.openxmlformats-officedocument.presentationml')
_DOCUMENT: str = (
    'application/vnd.openxmlformats-officedocument.wordprocessingml')
_MAIN_CONTENT_TYPES: dict[str, tuple[str, str]] = {
    '.potx': (f'{_PRESENTATION}.template.main+xml',
              f'{_PRESENTATION}.presentation.main+xml'),
    '.dotx': (f'{_DOCUMENT}.template.main+xml',
              f'{_DOCUMENT}.document.main+xml')}
_RELATIONSHIPS: str = (
    'http://schemas.openxmlformats.org/officeDocument/2006/relationships')
# Parts that a presentation needs but an Office theme does not include. Each
# value is the content, content type, and relationship type of the part.
_PRESENTATION_NAMESPACES: str = (
    'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
    f'xmlns:r="{_RELATIONSHIPS}" '
    'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')
_XML_DECLARATION: str = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
_THEME_EXTRA_PARTS: dict[str, tuple[str, str, str]] = {
    'ppt/presProps.xml': (
        f'{_XML_DECLARATION}<p:presentationPr {_PRESENTATION_NAMESPACES}/>',
        f'{_PRESENTATION}.presProps+xml',
        'presProps'),
    'ppt/viewProps.xml': (
        f'{_XML_DECLARATION}<p:viewPr {_PRESENTATION_NAMESPACES}/>',
        f'{_PRESENTATION}.viewProps+xml',
        'viewProps'),
    'ppt/tableStyles.xml': (
        (f'{_XML_DECLARATION}<a:tblStyleLst xmlns:a="http://schemas.'
         'openxmlformats.org/drawingml/2006/main" '
         'def="{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}"/>'),
        f'{_PRESENTATION}.tableStyles+xml',
        'tableStyles')}
_HEADING_STYLES: tuple[str, ...] = (
    'Title', 'Subtitle', *(f'Heading {level}' for level in range(1, 10)))


""" Public Functions """


def create_word_template(
        formatting: styles.Formatting,
        destination: str | pathlib.Path) -> pathlib.Path:
    """Creates a Word reference document with `formatting` applied.

    The document starts as pandoc's default reference document. Footnotes are
    numbered continuously instead of restarting in each section (which
    LibreOffice treats as restarting at each top level heading).

    Args:
        formatting: the formatting to apply.
        destination: path for the created document.

    Returns:
        The path to the created document.

    """
    destination = pathlib.Path(destination)
    destination.write_bytes(get_pandoc_template('docx'))
    document = docx.Document(str(destination))
    _apply_formatting(document, formatting)
    _number_footnotes_continuously(document)
    document.save(str(destination))
    return destination


def find_template(
        name: str,
        application: str,
        folder: str | pathlib.Path) -> pathlib.Path:
    """Returns the path to the template for `name`.

    Args:
        name: a path to a template (absolute or relative to `folder`) or the
            name of a template without its extension.
        application: 'word', 'powerpoint', or 'csl'.
        folder: the project folder.

    Returns:
        The path to the template.

    Raises:
        FileNotFoundError: if no template is found for `name`.
        ValueError: if `application` is not 'word', 'powerpoint', or 'csl' or
            the template has the wrong extension.

    """
    if application not in _EXTENSIONS:
        message = f'unknown application "{application}"'
        raise ValueError(message)
    extensions = _EXTENSIONS[application]
    path = pathlib.Path(folder) / pathlib.Path(name).expanduser()
    if path.suffix:
        if path.suffix.lower() not in extensions:
            message = (
                f'{path.name} is not a {application} template (use '
                f'{", ".join(extensions)})')
            raise ValueError(message)
        if path.is_file():
            return path
    else:
        for base in (pathlib.Path(folder), _TEMPLATES_FOLDER / application):
            for extension in extensions:
                candidate = base / f'{name}{extension}'
                if candidate.is_file():
                    return candidate
    included = ', '.join(list_templates(application)) or 'none'
    message = (
        f'{application} template "{name}" not found (included templates: '
        f'{included})')
    raise FileNotFoundError(message)


def get_pandoc_template(extension: str) -> bytes:
    """Returns pandoc's default reference document.

    Args:
        extension: 'docx' or 'pptx'.

    Returns:
        The contents of the reference document.

    """
    # 'shell' is `False` (the default) so that `subprocess` is used securely.
    process = subprocess.run(  # noqa: S603
        [pypandoc.get_pandoc_path(), '--print-default-data-file',
         f'reference.{extension}'],
        capture_output = True,
        check = True)
    return process.stdout


def list_templates(application: str) -> list[str]:
    """Returns the names of the templates included with `coursebook`.

    Args:
        application: 'word', 'powerpoint', or 'csl'.

    Returns:
        The names of the included templates, without their extensions.

    """
    folder = _TEMPLATES_FOLDER / application
    if not folder.is_dir():
        return []
    extensions = _EXTENSIONS.get(application, ())
    return sorted(
        path.stem for path in folder.iterdir()
        if path.suffix.lower() in extensions)


def prepare_template(
        path: str | pathlib.Path,
        destination: str | pathlib.Path) -> pathlib.Path:
    """Converts a template into a reference document that pandoc can use.

    Args:
        path: path to a '.docx', '.dotx', '.pptx', '.potx', or '.thmx' file.
        destination: folder for a converted template.

    Returns:
        `path` if it is already a '.docx' or '.pptx' file. Otherwise, the
            path to the converted template in `destination`.

    Raises:
        ValueError: if `path` does not have a supported extension.

    """
    path = pathlib.Path(path)
    suffix = path.suffix.lower()
    if suffix in {'.docx', '.pptx'}:
        return path
    extension = '.docx' if suffix == '.dotx' else '.pptx'
    destination = pathlib.Path(destination)
    destination.mkdir(parents = True, exist_ok = True)
    converted = destination / f'{path.stem}{extension}'
    if suffix in _MAIN_CONTENT_TYPES:
        _convert_office_template(path, converted)
    elif suffix == '.thmx':
        _convert_theme(path, converted)
    else:
        message = f'{path.name} is not a Word or PowerPoint template'
        raise ValueError(message)
    return converted


""" Private Functions """


def _apply_formatting(
        document: Document,
        formatting: styles.Formatting) -> None:
    """Applies `formatting` to the styles of a Word document.

    Args:
        document: the Word document to change.
        formatting: the formatting to apply.

    """
    document_styles = document.styles
    if formatting.body_font:
        _set_default_font(document, formatting.body_font)
        _set_font(document_styles['Normal'], formatting.body_font)
    if formatting.font_size:
        document_styles['Normal'].font.size = Pt(formatting.font_size)
    body = document_styles['Body Text']
    if formatting.line_spacing:
        body.paragraph_format.line_spacing = formatting.line_spacing
    if formatting.first_line_indent:
        body.paragraph_format.first_line_indent = Inches(
            formatting.first_line_indent)
        # The first paragraph under a heading is traditionally not indented.
        first = document_styles['First Paragraph'].paragraph_format
        first.first_line_indent = Inches(0)
    footnote = document_styles['Footnote Text']
    if formatting.footnote_size:
        footnote.font.size = Pt(formatting.footnote_size)
        footnote.paragraph_format.line_spacing = 1.0
    heading_font = formatting.heading_font or formatting.body_font
    for name in _HEADING_STYLES:
        style = document_styles[name]
        if heading_font:
            _set_font(style, heading_font)
        if formatting.heading_color:
            style.font.color.rgb = RGBColor.from_string(
                formatting.heading_color)
    top = document_styles['Heading 1']
    if formatting.center_top_headings:
        top.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if formatting.capitalize_top_headings:
        top.font.all_caps = True
    section = document.sections[0]
    if formatting.margins is not None:
        margin = Inches(formatting.margins)
        section.left_margin = section.right_margin = margin
        section.top_margin = section.bottom_margin = margin
    if formatting.page_numbers:
        _add_page_numbers(section)


def _add_page_numbers(section: Section) -> None:
    """Adds a centered page number to the footer of a Word section.

    Args:
        section: the Word section to change.

    """
    paragraph = section.footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()._r
    begin = OxmlElement('w:fldChar')
    begin.set(qn('w:fldCharType'), 'begin')
    instruction = OxmlElement('w:instrText')
    instruction.set(qn('xml:space'), 'preserve')
    instruction.text = 'PAGE'
    end = OxmlElement('w:fldChar')
    end.set(qn('w:fldCharType'), 'end')
    run.extend([begin, instruction, end])


def _convert_office_template(
        source: pathlib.Path,
        destination: pathlib.Path) -> None:
    """Converts a '.dotx' or '.potx' template to a '.docx' or '.pptx' file.

    The only difference between a template and a document is the content type
    of its main part.

    Args:
        source: path to the template.
        destination: path for the converted file.

    """
    old, new = _MAIN_CONTENT_TYPES[source.suffix.lower()]
    with (
            zipfile.ZipFile(source) as original,
            zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as copy):
        for info in original.infolist():
            data = original.read(info.filename)
            if info.filename == '[Content_Types].xml':
                data = data.replace(old.encode(), new.encode())
            copy.writestr(info, data)


def _convert_theme(source: pathlib.Path, destination: pathlib.Path) -> None:
    """Converts a '.thmx' Office theme to a '.pptx' file.

    An Office theme stores a presentation without slides in a 'theme' folder.
    A '.pptx' file stores it in a 'ppt' folder. So, the parts are moved, the
    parts that are only used by themes are dropped, and the parts that a
    presentation needs but a theme lacks are added.

    Args:
        source: path to the '.thmx' file.
        destination: path for the '.pptx' file.

    Raises:
        ValueError: if `source` is not an Office theme with a presentation.

    """
    with zipfile.ZipFile(source) as theme:
        names = theme.namelist()
        if 'theme/presentation.xml' not in names:
            message = f'{source.name} does not include a slide master'
            raise ValueError(message)
        with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as deck:
            for name in names:
                data = theme.read(name)
                if name.startswith('theme/theme/') and (
                        'themeManager' in name or 'Thumbnail' in name):
                    continue
                if name == '[Content_Types].xml':
                    deck.writestr(name, _convert_theme_content_types(data))
                elif name == '_rels/.rels':
                    text = re.sub(
                        r'Target="theme/theme/themeManager\.xml"',
                        'Target="ppt/presentation.xml"',
                        data.decode('utf-8'))
                    deck.writestr(name, text)
                elif name == 'theme/_rels/presentation.xml.rels':
                    deck.writestr(
                        'ppt/_rels/presentation.xml.rels',
                        _convert_theme_relationships(data))
                elif name.startswith('theme/'):
                    deck.writestr(f'ppt/{name.removeprefix("theme/")}', data)
                else:
                    deck.writestr(name, data)
            for part, (content, _, _) in _THEME_EXTRA_PARTS.items():
                deck.writestr(part, content)


def _convert_theme_content_types(data: bytes) -> str:
    """Converts the content types of an Office theme to a presentation's.

    Args:
        data: the '[Content_Types].xml' part of a '.thmx' file.

    Returns:
        The content types for the converted presentation.

    """
    text = re.sub(
        r'<Override PartName="/theme/theme/themeManager\.xml"[^>]*/>',
        '',
        data.decode('utf-8'))
    text = text.replace('PartName="/theme/', 'PartName="/ppt/')
    overrides = ''.join(
        f'<Override PartName="/{part}" ContentType="{content_type}"/>'
        for part, (_, content_type, _) in _THEME_EXTRA_PARTS.items())
    return text.replace('</Types>', f'{overrides}</Types>')


def _convert_theme_relationships(data: bytes) -> str:
    """Adds the relationships that a presentation needs to an Office theme's.

    Args:
        data: the 'theme/_rels/presentation.xml.rels' part of a '.thmx' file.

    Returns:
        The relationships for the converted presentation.

    """
    relationships = [(
        f'<Relationship Id="rIdCourseTheme" Type="{_RELATIONSHIPS}/theme" '
        'Target="theme/theme1.xml"/>')]
    for index, (part, (_, _, kind)) in enumerate(_THEME_EXTRA_PARTS.items()):
        target = part.removeprefix('ppt/')
        relationships.append(
            f'<Relationship Id="rIdCourse{index}" '
            f'Type="{_RELATIONSHIPS}/{kind}" Target="{target}"/>')
    return data.decode('utf-8').replace(
        '</Relationships>', f'{"".join(relationships)}</Relationships>')


def _number_footnotes_continuously(document: Document) -> None:
    """Sets the footnotes of a Word document to be numbered continuously.

    Args:
        document: the Word document to change.

    """
    properties = document.sections[0]._sectPr
    footnotes = properties.find(qn('w:footnotePr'))
    if footnotes is None:
        footnotes = OxmlElement('w:footnotePr')
        references = [
            child for child in properties
            if child.tag in {qn('w:headerReference'), qn('w:footerReference')}]
        if references:
            references[-1].addnext(footnotes)
        else:
            properties.insert(0, footnotes)
    restart = footnotes.find(qn('w:numRestart'))
    if restart is None:
        # 'w:numRestart' is the last element that a 'w:footnotePr' in a
        # section may have.
        restart = OxmlElement('w:numRestart')
        footnotes.append(restart)
    restart.set(qn('w:val'), 'continuous')


def _set_default_font(document: Document, font: str) -> None:
    """Sets the default font of a Word document.

    Args:
        document: the Word document to change.
        font: the name of the font.

    """
    defaults = document.styles.element.find(qn('w:docDefaults'))
    if defaults is None:
        return
    properties = defaults.find(qn('w:rPrDefault'))
    if properties is None:
        return
    run = properties.find(qn('w:rPr'))
    fonts = None if run is None else run.find(qn('w:rFonts'))
    if fonts is not None:
        _replace_theme_fonts(fonts, font)


def _set_font(style: ParagraphStyle, font: str) -> None:
    """Sets the font of a Word style, replacing any theme fonts.

    Word uses a theme font (such as 'majorHAnsi') instead of a named font when
    both are set. So, the theme fonts are removed.

    Args:
        style: the Word style to change.
        font: the name of the font.

    """
    style.font.name = font
    fonts = style.element.rPr.find(qn('w:rFonts'))
    _replace_theme_fonts(fonts, font)


def _replace_theme_fonts(fonts: BaseOxmlElement, font: str) -> None:
    """Replaces the theme fonts in a 'w:rFonts' element with `font`.

    Args:
        fonts: the 'w:rFonts' element.
        font: the name of the font.

    """
    for attribute in ('asciiTheme', 'hAnsiTheme', 'eastAsiaTheme', 'cstheme'):
        fonts.attrib.pop(qn(f'w:{attribute}'), None)
    for attribute in ('ascii', 'hAnsi', 'eastAsia', 'cs'):
        fonts.set(qn(f'w:{attribute}'), font)
