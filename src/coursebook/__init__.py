"""Turns markdown files into coursebooks, slides, and teaching notes.

Contents:
    Book: style for a book with accompanying slides.
    Coursebook: style for a coursebook with slides and teaching notes.
    ExportOptions: options shared by every exporter.
    Formatting: formatting of the text and notes.
    HtmlExporter: exports a document to a single HTML file.
    Exporter: base class for exporters.
    LawReview: style for a law review article with accompanying slides.
    Outline: the entries of a project in order.
    OutlineEntry: a single entry in an outline.
    PdfExporter: exports a document to a PDF file.
    PowerPointExporter: exports a slide deck to a PowerPoint file.
    Project: the settings, outline, sources, and style of a project.
    Settings: the options in the "Project" section of a project file.
    Source: the front matter and sections of a source file.
    Style: base class for styles.
    WordExporter: exports a document to a Word file.
    build: builds the files of the project in a folder.
    get_exporter: returns the exporter with a name.
    get_style: returns the style with a name.

"""

from __future__ import annotations

__version__ = '0.1.0'

__author__: str = 'Corey Rayburn Yung'

__all__: list[str] = [
    'Book',
    'Coursebook',
    'ExportOptions',
    'Exporter',
    'Formatting',
    'HtmlExporter',
    'LawReview',
    'Outline',
    'OutlineEntry',
    'PdfExporter',
    'PowerPointExporter',
    'Project',
    'Settings',
    'Source',
    'Style',
    'WordExporter',
    'build',
    'get_exporter',
    'get_style']

from .exporters import (
    ExportOptions,
    Exporter,
    HtmlExporter,
    PdfExporter,
    PowerPointExporter,
    WordExporter,
    get_exporter,
)
from .outline import Outline, OutlineEntry
from .project import Project, build
from .settings import Settings
from .sources import Source
from .styles import Book, Coursebook, Formatting, LawReview, Style, get_style
