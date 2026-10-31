# coursebook

<p align="center">
<img src="https://github.com/WithPrecedent/coursebook/blob/main/docs/images/logo.jfif?raw=true" alt="logo" style="width:200px;"/>
</p>

| | |
| --- | --- |
| Version | [![PyPI Latest Release](https://img.shields.io/pypi/v/coursebook.svg?style=for-the-badge&color=cornflowerblue&label=PyPI&logo=PyPI&logoColor=yellow)](https://pypi.org/project/coursebook/) [![GitHub Latest Release](https://img.shields.io/github/v/tag/WithPrecedent/coursebook?style=for-the-badge&color=forestgreen&label=GitHub&logo=github)](https://github.com/WithPrecedent/coursebook/releases) |
| Status | [![Build Status](https://img.shields.io/github/actions/workflow/status/WithPrecedent/coursebook/ci.yml?style=for-the-badge&branch=main&color=cadetblue&label=Tests&logo=pytest)](https://github.com/WithPrecedent/coursebook/actions/workflows/ci.yml?query=branch%3Amain) [![Code Coverage](https://img.shields.io/codecov/c/github/WithPrecedent/coursebook?style=for-the-badge&color=cadetblue&label=Coverage&logo=codecov)](https://app.codecov.io/gh/WithPrecedent/coursebook) [![Development Status](https://img.shields.io/badge/Development-Active-seagreen?style=for-the-badge&logo=git)](https://www.repostatus.org/#active) [![Project Stability](https://img.shields.io/pypi/status/coursebook?style=for-the-badge&logo=pypi&label=Stability&logoColor=yellow)](https://pypi.org/project/coursebook/) |
| Documentation | [![Hosted By](https://img.shields.io/badge/Hosted_by-Github_Pages-blue?style=for-the-badge&color=forestgreen&logo=github)](https://WithPrecedent.github.io/coursebook) |
| Tools | [![Documentation](https://img.shields.io/badge/MkDocs-magenta?style=for-the-badge&color=deepskyblue&logo=markdown&labelColor=gray)](https://squidfunk.github.io/mkdocs-material/) [![Linter](https://img.shields.io/endpoint?style=for-the-badge&url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![Type Checker](https://img.shields.io/badge/mypy-steelblue?style=for-the-badge&logo=python&logoColor=white&labelColor=gray)](https://mypy-lang.org/) [![Dependency Manager](https://img.shields.io/badge/uv-mediumpurple?style=for-the-badge&logo=uv&labelColor=gray)](https://docs.astral.sh/uv/) [![Pre-commit](https://img.shields.io/badge/pre--commit-darkolivegreen?style=for-the-badge&logo=pre-commit&logoColor=white&labelColor=gray)](https://pre-commit.com/) [![CI](https://img.shields.io/badge/GitHub_Actions-forestgreen?style=for-the-badge&logo=githubactions&labelColor=gray&logoColor=white)](https://github.com/features/actions) [![Editor Settings](https://img.shields.io/badge/Editor_Config-paleturquoise?style=for-the-badge&logo=editorconfig&labelColor=gray)](https://editorconfig.org/) [![Repository Template](https://img.shields.io/badge/snickerdoodle-bisque?style=for-the-badge&logo=cookiecutter&labelColor=gray)](https://www.github.com/WithPrecedent/snickerdoodle) [![Dependency Maintainer](https://img.shields.io/badge/dependabot-forestgreen?style=for-the-badge&logo=dependabot&logoColor=white&labelColor=gray)](https://github.com/dependabot) |
| Compatibility | [![Compatible Python Versions](https://img.shields.io/pypi/pyversions/coursebook?style=for-the-badge&color=cornflowerblue&label=Python&logo=python&logoColor=yellow)](https://pypi.org/project/coursebook/) [![Linux](https://img.shields.io/badge/Linux-lightseagreen?style=for-the-badge&logo=linux&labelColor=gray&logoColor=white)](https://www.linux.org/) [![MacOS](https://img.shields.io/badge/MacOS-antiquewhite?style=for-the-badge&logo=apple&labelColor=gray)](https://www.apple.com/macos/) [![Windows](https://img.shields.io/badge/Windows-blue?style=for-the-badge)](https://www.microsoft.com/en-us/windows?r=1) |
| Stats | [![PyPI Download Rate (per month)](https://img.shields.io/pypi/dm/coursebook?style=for-the-badge&color=cornflowerblue&label=Downloads%20💾&logo=pypi&logoColor=yellow)](https://pypi.org/project/coursebook/) [![GitHub Stars](https://img.shields.io/github/stars/WithPrecedent/coursebook?style=for-the-badge&color=forestgreen&label=Stars%20⭐&logo=github)](https://github.com/WithPrecedent/coursebook/stargazers) [![GitHub Contributors](https://img.shields.io/github/contributors/WithPrecedent/coursebook?style=for-the-badge&color=forestgreen&label=Contributors%20🙋&logo=github)](https://github.com/WithPrecedent/coursebook/graphs/contributors) [![GitHub Issues](https://img.shields.io/github/issues/WithPrecedent/coursebook?style=for-the-badge&color=forestgreen&label=Issues%20📘&logo=github)](https://github.com/WithPrecedent/coursebook/issues) [![GitHub Forks](https://img.shields.io/github/forks/WithPrecedent/coursebook?style=for-the-badge&color=forestgreen&label=Forks%20🍴&logo=github)](https://github.com/WithPrecedent/coursebook/forks) |
| | |

-----


-----

## What is coursebook?

`coursebook` turns a folder of markdown files into the materials for a course
or publication: a Word, PDF, or HTML document with the text, a PowerPoint deck
with accompanying slides, and a document of teaching notes. You write each
part of your project once, in plain markdown, with its text, slides, and notes
side by side. A short project file sets the order of the parts and how the
results should look.

## Why use coursebook?

* **One source for everything:** the text, slides, and notes for each chapter
  or section live in the same markdown file, so they stay in sync.
* **Outlines you already know:** the structure of a project is a traditional
  outline (I, A, 1, a, i). Headings and their levels come from it.
* **Microsoft Office output:** Word and PowerPoint files are styled with
  templates, including Word (`.docx`, `.dotx`) and PowerPoint (`.pptx`,
  `.potx`) templates and Office themes (`.thmx`).
* **PDF and HTML too:** the text and notes can also be exported to PDF
  (without LaTeX) and to a single, self-contained HTML file, at the same time
  as Word.
* **Academic features:** footnotes, citations from BibTeX or other
  bibliography files (with Bluebook citations for law reviews), tables, math,
  and images, all through [pandoc](https://pandoc.org/).
* **Styles for academic work:** built-in styles for coursebooks, books, and
  law review articles, and an easy way to add your own.
* **Nothing else to install:** a copy of pandoc is included.

`coursebook` is not a word processor. If you need tracked changes or
comments from co-authors, export with `coursebook` and continue in Word.

## Getting started

### Requirements

`coursebook` requires Python 3.11 or later and runs on Linux, macOS, and
Windows. Any text editor works for writing the markdown files.

### Installation

To install `coursebook`, use `pip`:

```sh
pip install coursebook
```

PDF export needs one more package, which this installs:

```sh
pip install "coursebook[pdf]"
```

### Usage

#### Starting a project

`coursebook new` creates a project folder with a project file, a source file
for each outline entry, and a "visuals" folder:

```sh
coursebook new my_course --style coursebook --entry "I: Introduction" --entry "II: Negligence"
```

Instead of `--entry`, you can pass `--outline outline.txt`, a text file with
one outline line per line. Use `--format toml` or `--format yaml` for a `toml`
or `yaml` project file. Without an outline, a short sample outline is used.
Existing source files are never overwritten.

#### Project folders

A project is a folder with a project file, one markdown file for each entry
in the outline, and (optionally) a "visuals" folder with images:

```text
my_course/
├── project.ini
├── introduction.md
├── literature_review.md
├── ...
└── visuals/
    └── chart.png
```

#### The project file

The project file is named "project" and may be an `ini`, `toml`, or `yaml`
file. Its "Project" section holds settings and its "Outline" section holds
the structure of the project:

```ini
[Project]
Name: Crazy Idea
Author: Corey Rayburn Yung
Style: coursebook
Include: text, slides, notes
Slides Template: chalkboard
Output Folder: output

[Outline]
I: Introduction
II: Literature Review
III: My Cool Idea
A: Interesting Premise 1
1: Underlying Facts
2: Supporting Work
B: Interesting Premise 2
IV: Conclusion
```

The level of each outline entry comes from its label: upper case Roman
numerals (I), upper case letters (A), numbers (1), lower case letters (a), and
lower case Roman numerals (i), in whatever order you nest them. A book can
number its chapters with "1", "2", and so on. Labels may repeat under
different parents (an "A" under "I" and another under "II"). If you skip a
label (such as going from "A" to "C"), `coursebook` warns you but keeps going.
After "h", an "i" continues the letters.

Entries without numbers, such as a preface or an appendix, use dashes as
their labels: `-` for the top level, `--` for the level below it, and so on.
The numbering of the other entries continues around them:

```ini
[Outline]
-: Preface
I: Introduction
II: Argument
-: Appendix
A: Data
```

An entry can name its own source file after a `|`, which is useful for files
in subfolders or for entries that share a title:

```ini
I: Introduction | chapters/intro.md
A: Overview | intro_overview.md
II: Negligence
A: Overview | negligence_overview.md
```

In a `toml` or `yaml` file, the outline is a list (of lines or of
`[label, title, file]` lists):

```toml
outline = [
    "I: Introduction",
    "II: Background",
    "A: History",
    "B: Current Law"]

[project]
name = "A Modest Proposal"
style = "law review"
```

#### Settings

Setting names ignore case, spaces, and underscores ("Output Folder",
"output_folder", and "OUTPUT FOLDER" are the same).

| Setting | Default | Meaning |
| --- | --- | --- |
| Name | Untitled | Title of the project, also used to name the created files |
| Subtitle, Date | | Shown on the title page and title slide |
| Author | | Authors, separated by semicolons |
| Style | coursebook | `coursebook` (or `textbook`), `book`, or `law review` |
| Include | from the style | Sections to create: `text`, `slides`, and/or `notes` |
| Output Folder | output | Where the files are created |
| Visuals Folder | visuals | Where images are found |
| Text Template | from the style | Word template for the text |
| Slides Template | chalkboard | PowerPoint template or theme for the slides |
| Notes Template | the text template | Word template for the notes |
| Text Format | word | Formats for the text: `word`, `pdf`, and/or `html` |
| Slides Format | powerpoint | Format for the slides |
| Notes Format | word | Formats for the notes: `word`, `pdf`, and/or `html` |
| Bibliography | | Bibliography files for citations, separated by commas |
| CSL | from the style | [Citation style](https://www.zotero.org/styles) name or file |
| Table of Contents | from the style | Whether to add a table of contents |
| Number Headings | from the style | Whether headings include outline labels ("I. Introduction") |
| Section Slides | yes | Whether each outline entry gets a section title slide |
| Visuals In Notes | no | Whether images in the text are copied into the notes |

#### Source files

Each outline entry is matched to a markdown file named after its title, in
lower case with underscores for spaces and punctuation ("Interesting Premise
1" matches "interesting_premise_1.md"). An entry without a file still gets a
heading, and `coursebook` warns you that the file is missing.

A source file is divided into sections by lines with the section name in
angle brackets. Anything before the first divider is text:

```markdown
---
title: A Better Title Than the Outline's
visuals_in_notes: true
---

The text of the chapter, with a footnote.[^1]

# A Subheading

![Enrollment by year](chart.png){width=50%}

[^1]: Footnote labels only need to be unique within each file.

<slides>

# First Slide

- A point
- Another point

::: notes
Speaker notes for this slide.
:::

---

- A second slide, without a title

<notes>

Notes for the instructor's guide.
```

* **Front matter** (optional) may set `title` (used in place of the outline
  title) and `visuals_in_notes`.
* **Text:** write headings starting at `#`. They are placed beneath the
  heading for the outline entry.
* **Slides:** start each slide with a `#` heading or separate slides with
  `---`. If the slides do not start with a heading, the first slide is titled
  with the outline entry. Speaker notes go in `::: notes` blocks.
* **Notes:** like the text, but collected into a separate document.
  Entries without notes are left out of it.
* **Images** are found in the project folder and the visuals folder.
* **Citations** use pandoc's syntax (`[@scalia1997, 23]`) when the project
  has a bibliography. With a note style, such as the Bluebook style used by
  `law review`, each citation becomes a footnote.

#### Building

From the project folder, run:

```sh
coursebook
```

Or name the folder and choose the sections to create:

```sh
coursebook path/to/my_course --include slides --output-folder handouts
```

(`coursebook build` is the same command, and `python -m coursebook` works
too.) For the project above, `coursebook` creates "crazy_idea.docx",
"crazy_idea_slides.pptx", and "crazy_idea_notes.docx" in the output folder.
With `Text Format: word, pdf, html`, it also creates "crazy_idea.pdf" and
"crazy_idea.html".

When you open a Word document with a table of contents, Word asks whether to
update the fields in it; answer yes to fill in the table. PDF files use the
fonts installed on your computer, so a missing font (such as Georgia on some
Linux systems) is replaced with another one.

#### Styles

| Style | Sections | Headings | Formatting |
| --- | --- | --- | --- |
| `coursebook` | text, slides, notes | titles, table of contents | Georgia, 11 point, page numbers |
| `book` | text, slides | titles, table of contents | Georgia, 11 point, page numbers |
| `law review` | text, slides | labels ("I. Introduction"), centered and capitalized | Times New Roman, 12 point, double spaced, 10 point footnotes, one inch margins, page numbers, Bluebook citations |

A style's formatting is applied to pandoc's default Word template and passed
to the PDF and HTML files. If you name your own Word template, its formatting
is used for Word files instead.

#### Templates

A template setting may be a path (relative to the project folder) or a name
without an extension. A name is looked for first in the project folder and
then among the templates included with `coursebook` ("chalkboard"). Word
accepts `.docx` and `.dotx` files, and PowerPoint accepts `.pptx` and `.potx`
files and `.thmx` Office themes. A PowerPoint template must have the standard
layouts (Title Slide, Title and Content, Section Header, Two Content,
Comparison, Content with Caption, and Blank).

To start your own template from a style's, write it out, change it in Word or
PowerPoint, and name it in the project file:

```sh
coursebook template "law review" house_style.docx
coursebook template coursebook lecture.pptx
```

```ini
Text Template: house_style
Slides Template: lecture
```

The CSL setting works the same way: it may be a path to a `.csl` file or the
name of one, looked for in the project folder and then among the citation
styles included with `coursebook` ("bluebook-law-review"). Thousands of
citation styles are available from the [Zotero Style
Repository](https://www.zotero.org/styles).

#### Using Python

```python
import coursebook

project = coursebook.Project.from_folder('my_course')
print(project.missing)            # outline entries without a source file
print(project.assemble('slides')) # the combined markdown for the slides
project.build(include = ['text'])
```

New styles and export formats are registered when you subclass
`coursebook.Style` or `coursebook.Exporter`:

```python
import dataclasses

import coursebook


@dataclasses.dataclass
class Seminar(coursebook.Coursebook):
    number_headings: bool = True
    formatting: coursebook.Formatting = dataclasses.field(
        default_factory = lambda: coursebook.Formatting(
            body_font = 'Garamond', font_size = 12, page_numbers = True))
```

A project file can then use `Style: seminar`.

## Contributing

Contributors are always welcome. Feel free to grab an [issue](https://www.github.com/WithPrecedent/coursebook/issues) to work on or make a suggested improvement. If you wish to contribute, please read the [Contribution Guide](https://www.github.com/WithPrecedent/coursebook/blob/main/CONTRIBUTING.md) and [Code of Conduct](https://www.github.com/WithPrecedent/coursebook/blob/main/CODE_OF_CONDUCT.md).

## Similar Projects

* [quarto](https://quarto.org/): a publishing system that creates
  documents, presentations, websites, and books from markdown and notebooks.
* [pandoc](https://pandoc.org/): the document converter that `coursebook`
  uses to create its files.
* [Typst](https://typst.app/): the typesetting system that `coursebook` uses
  to create PDF files.

## Acknowledgments

I would like to thank the University of Kansas School of Law for tolerating and
supporting this law professor's coding efforts, an endeavor which is well
outside the typical scholarly activities in the discipline.

The included Bluebook citation style ("bluebook-law-review.csl") is from the
[Citation Style Language styles
repository](https://github.com/citation-style-language/styles). Its authors
are listed in the file, and it is licensed under the [Creative Commons
Attribution-ShareAlike 3.0
License](https://creativecommons.org/licenses/by-sa/3.0/).

## License

Use of this repository is authorized under the [Apache Software License 2.0](https://www.github.com/WithPrecedent/coursebook/blob/main/LICENSE).
