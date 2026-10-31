# Changelog

All notable changes to this project will be documented in this file.

<!-- insertion marker -->

## 0.1.0

* Renamed the package from `cento` to `coursebook` (the `cento` name is taken
  on PyPI).
* Updated the repository to the latest `snickerdoodle` template: `uv` and
  `hatchling` replace PDM, and CI runs the tests, `pre-commit`, `ruff`,
  `mypy`, Codecov, and the documentation build.
* Added the `coursebook` command (also `python -m coursebook`), with `build`
  (the default) to create a project's files, `new` to create a project folder
  with a project file and source files, and `template` to write a style's
  Word or PowerPoint template for editing.
* Added project files in `ini`, `toml`, and `yaml` formats. Outlines may
  repeat labels under different parents, and each entry's level comes from
  its label (I, A, 1, a, i). Entries may be unnumbered (`-: Preface`) and
  may name their own source files (`I: Introduction | chapters/intro.md`).
* Added source files with YAML front matter and `<text>`, `<slides>`, and
  `<notes>` sections.
* Added Word export for the text and notes and PowerPoint export for the
  slides, using a bundled copy of pandoc.
* Added PDF export (with Typst, through the `pdf` extra) and single-file HTML
  export for the text and notes. Each section may be exported to more than
  one format at once.
* Added the `coursebook`, `book`, and `law review` styles, which set headings,
  the table of contents, the citation style, and the formatting of Word, PDF,
  and HTML files (including margins and page numbers).
* Added the Bluebook law review citation style, which `law review` uses to
  turn citations into footnotes.
* Added Word (`.docx`, `.dotx`) and PowerPoint (`.pptx`, `.potx`, `.thmx`)
  templates, including the bundled "chalkboard" theme.
* Added footnotes that stay separate across source files (and are numbered
  continuously, including in LibreOffice), citations from bibliography files,
  images from a visuals folder, and speaker notes.
