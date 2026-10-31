"""The structure of a `coursebook` project.

An outline is a list of labeled titles, such as:

    I: Introduction
    II: The Problem
    A: History
    1: Early Cases
    2: Modern Cases
    B: Current Law
    III: Conclusion

The level of each entry comes from its label instead of from indentation. A
label can be an upper case Roman numeral (I), an upper case letter (A), an
Arabic number (1), a lower case letter (a), or a lower case Roman numeral (i).
An entry is placed:

1. after the deepest earlier entry whose next label it is (so 'B' follows
    'A'); or, if there is none,
2. beneath the previous entry if it is the first label of a kind that is not
    used by the previous entry or its parents (so 'A' or '1' opens a new
    level); or, if neither applies,
3. after the deepest earlier entry with the same kind of label, even if some
    labels were skipped (so 'C' can follow 'A'), with a warning.

Because of the first rule, 'i' after 'h' continues the lower case letters
instead of starting lower case Roman numerals.

An entry without a number (such as a preface or an appendix) has a label of
dashes: '-' for the top level, '--' for the level below it, and so on. An
unnumbered entry takes the place of a numbered one in the outline, so the
numbering continues after it. A numbered label that opens a new level after an
unnumbered entry is placed at the level of the unnumbered entry instead of
beneath it.

Each entry is matched to the source file named after its title. To use
another file, add it after a '|' (the file name must end with '.md'):

    I: Introduction | chapters/intro.md

Contents:
    Outline: the entries of a project in order.
    OutlineEntry: a single entry in an outline.
    OutlineLine: type of an outline line or a tuple of its parts.
    parse_outline_line: splits an outline line into its label, title, and
        file.
    _LABEL_KINDS: the kinds of labels that may be used in an outline, each
        with a function that creates a label from a number and a function that
        returns the number of a label (or `None`).
    _LOGGER: logger for warnings about skipped labels.
    _Stack: type of the open entries while an outline is read.
    _ROMAN_NUMERALS: Roman numeral symbols and their values.

"""

from __future__ import annotations

import dataclasses
import logging
import pathlib
import string
from typing import TYPE_CHECKING, TypeAlias

from . import markdown

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator

OutlineLine: TypeAlias = str | tuple[str, ...]
# Each item is an open entry and the kind and number of the labels at its level
# (or `None` for an unnumbered level).
_Stack: TypeAlias = 'list[tuple[OutlineEntry, int | None, int]]'
_LOGGER = logging.getLogger(__name__)
_ROMAN_NUMERALS: tuple[tuple[int, str], ...] = (
    (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'), (100, 'C'),
    (90, 'XC'), (50, 'L'), (40, 'XL'), (10, 'X'), (9, 'IX'), (5, 'V'),
    (4, 'IV'), (1, 'I'))


@dataclasses.dataclass
class OutlineEntry:
    """A single entry in an outline.

    Args:
        label: the label of the entry as written in the outline (such as 'IV'
            or 'b'), without any trailing period or surrounding parentheses.
            An unnumbered entry has an empty label.
        title: the title of the entry.
        level: depth of the entry in the outline, starting at 0 for the top
            level. Defaults to 0.
        file: path to the source file, relative to the project folder.
            Defaults to `None`, which uses a file named after `title`.
        children: entries directly beneath this entry. Defaults to an empty
            `list`.

    """

    label: str
    title: str
    level: int = 0
    file: str | None = None
    children: list[OutlineEntry] = dataclasses.field(default_factory = list)

    """ Properties """

    @property
    def file_name(self) -> str:
        """Returns the path to the source file, relative to the project folder.

        Returns:
            `file`, or the name of the entry with the '.md' extension.

        """
        return self.file or f'{self.name}.md'

    @property
    def name(self) -> str:
        """Returns the name of the source for this entry.

        Returns:
            The path of `file` without its extension, or `title`, in lower case
                with words joined by underscores.

        """
        if self.file:
            path = pathlib.PurePosixPath(self.file.replace('\\', '/'))
            return markdown.normalize_name(str(path.with_suffix('')))
        return markdown.normalize_name(self.title)

    @property
    def numbered(self) -> bool:
        """Returns whether the entry has a numbered label.

        Returns:
            Whether `label` is not empty.

        """
        return bool(self.label)

    """ Public Methods """

    def walk(self) -> Iterator[OutlineEntry]:
        """Yields this entry and every entry beneath it, in outline order.

        Yields:
            This entry, followed by each entry beneath it (depth first).

        """
        yield self
        for child in self.children:
            yield from child.walk()


@dataclasses.dataclass
class Outline:
    """The entries of a project in order.

    Args:
        entries: the top level entries of the outline. Each entry stores the
            entries beneath it in its `children`. Defaults to an empty `list`.

    """

    entries: list[OutlineEntry] = dataclasses.field(default_factory = list)

    """ Class Methods """

    @classmethod
    def from_lines(cls, lines: Iterable[OutlineLine]) -> Outline:
        """Creates an outline from labeled lines.

        Args:
            lines: each item is either a line from an outline (such as
                'A: History') or a `tuple` of a label, a title, and
                (optionally) a file. Blank lines are skipped.

        Returns:
            An outline with the level of each entry set from its label.

        Raises:
            ValueError: if a line has no label or title, or if a label cannot
                be placed in the outline.

        """
        outline = cls()
        # The last item is the most recent entry.
        stack: _Stack = []
        for line in lines:
            if isinstance(line, str):
                if not line.strip():
                    continue
                label, title, file = parse_outline_line(line)
            else:
                label, title, file = _parse_parts(line)
            if _is_unnumbered(label):
                depth, kind, number = _place_unnumbered(label, title, stack)
                label = ''
            else:
                depth, kind, number = _place_label(label, stack)
            entry = OutlineEntry(
                label = label, title = title, level = depth, file = file)
            del stack[depth:]
            if depth == 0:
                outline.entries.append(entry)
            else:
                stack[-1][0].children.append(entry)
            stack.append((entry, kind, number))
        return outline

    """ Public Methods """

    def walk(self) -> Iterator[OutlineEntry]:
        """Yields every entry in the outline, in order.

        Yields:
            Each entry in the outline (depth first).

        """
        for entry in self.entries:
            yield from entry.walk()

    """ Dunder Methods """

    def __iter__(self) -> Iterator[OutlineEntry]:
        """Yields every entry in the outline, in order.

        Returns:
            An iterator of each entry in the outline (depth first).

        """
        return self.walk()

    def __len__(self) -> int:
        """Returns the number of entries in the outline at every level.

        Returns:
            The number of entries.

        """
        return sum(1 for _ in self.walk())


""" Public Functions """


def parse_outline_line(line: str) -> tuple[str, str, str | None]:
    """Splits a line from an outline into its label, title, and file.

    The label and title may be separated by ':' or '=' (the same separators
    allowed in an `ini` file). A file may follow the title after a '|'.

    Args:
        line: a line from an outline (such as 'A: History' or
            'A: History | history_notes.md').

    Returns:
        The label (without any trailing period or surrounding parentheses),
            the title, and the file (or `None`).

    Raises:
        ValueError: if `line` does not have both a label and a title.

    """
    positions = [line.find(mark) for mark in ':=' if mark in line]
    if not positions:
        message = f'outline line "{line.strip()}" needs a label and a title'
        raise ValueError(message)
    split = min(positions)
    return _parse_parts((line[:split], line[split + 1:]), line)


""" Private Functions """


def _split_file(title: str) -> tuple[str, str | None]:
    """Separates a file at the end of `title` (after a '|').

    Args:
        title: the title part of an outline line.

    Returns:
        The title and the file, or `title` and `None` if it does not end with
            a '|' followed by a file name ending in '.md'.

    """
    before, separator, after = title.rpartition('|')
    if separator and after.strip().lower().endswith('.md'):
        return before.strip(), after.strip()
    return title.strip(), None


def _parse_parts(
        parts: tuple[str, ...],
        line: str | None = None) -> tuple[str, str, str | None]:
    """Returns the label, title, and file from the parts of an outline line.

    Args:
        parts: a label and a title, and optionally a file. If there is no
            file, the title may end with one (after a '|').
        line: the original line, for error messages. Defaults to `None`.

    Returns:
        The label, title, and file (or `None`).

    Raises:
        ValueError: if a label or title is missing or there are too many
            parts.

    """
    text = line.strip() if line is not None else ' | '.join(map(str, parts))
    if len(parts) not in {2, 3}:
        message = f'outline line "{text}" needs a label and a title'
        raise ValueError(message)
    label = _clean_label(str(parts[0]))
    if len(parts) == 3:  # noqa: PLR2004
        title, file = str(parts[1]).strip(), str(parts[2]).strip() or None
    else:
        title, file = _split_file(str(parts[1]))
    if not label or not title:
        message = f'outline line "{text}" needs a label and a title'
        raise ValueError(message)
    return label, title, file


def _clean_label(label: str) -> str:
    """Removes a trailing period and surrounding parentheses from `label`.

    Args:
        label: a label as written in an outline (such as 'A.' or '(1)').

    Returns:
        The label without the extra characters.

    """
    label = str(label).strip().rstrip('.')
    if label.startswith('('):
        label = label[1:]
    return label.rstrip(')').strip()


def _is_unnumbered(label: str) -> bool:
    """Returns whether `label` marks an unnumbered entry.

    Args:
        label: a label from an outline.

    Returns:
        Whether `label` is only dashes.

    """
    return bool(label) and set(label) == {'-'}


def _letters(number: int, alphabet: str) -> str:
    """Returns the outline letter label for `number`.

    After 'Z', labels double the letter ('AA', 'BB', and so on).

    Args:
        number: the position of the label, starting at 1.
        alphabet: the 26 letters to use.

    Returns:
        The letter label.

    """
    return alphabet[(number - 1) % 26] * ((number - 1) // 26 + 1)


def _parse_letters(label: str, alphabet: str) -> int | None:
    """Returns the position of a letter label, if it is one.

    Args:
        label: a label from an outline.
        alphabet: the 26 letters that may be used.

    Returns:
        The position of `label` (starting at 1), or `None` if `label` is not a
            letter label.

    """
    if not label or label[0] not in alphabet or set(label) != {label[0]}:
        return None
    return alphabet.index(label[0]) + 1 + 26 * (len(label) - 1)


def _parse_number(label: str) -> int | None:
    """Returns the value of an Arabic number label, if it is one.

    Args:
        label: a label from an outline.

    Returns:
        The value of `label`, or `None` if `label` is not a positive number.

    """
    if label.isdigit() and int(label) > 0:
        return int(label)
    return None


def _parse_roman(label: str) -> int | None:
    """Returns the value of an upper case Roman numeral label, if it is one.

    Args:
        label: a label from an outline.

    Returns:
        The value of `label`, or `None` if `label` is not a Roman numeral in
            standard form.

    """
    if not label or set(label) - set('MDCLXVI'):
        return None
    total, rest = 0, label
    for value, symbol in _ROMAN_NUMERALS:
        while rest.startswith(symbol):
            total += value
            rest = rest[len(symbol):]
    if rest or _roman(total) != label:
        return None
    return total


def _place_label(
        label: str,
        stack: _Stack) -> tuple[int, int, int]:
    """Returns where the entry with `label` belongs in the outline.

    The rules are described in the module docstring.

    Args:
        label: the label of the new entry.
        stack: the open entries, from the top level down to the most recent
            entry, each with the kind and number of the labels at its level.

    Returns:
        The level of the new entry and the kind (an index of `_LABEL_KINDS`)
            and number of its label.

    Raises:
        ValueError: if `label` cannot be placed in the outline.

    """
    numbered = [
        (depth, kind, number) for depth, (_, kind, number) in enumerate(stack)
        if kind is not None]
    for depth, kind, number in reversed(numbered):
        if _LABEL_KINDS[kind][0](number + 1) == label:
            return depth, kind, number + 1
    used = {kind for _, kind, _ in numbered}
    # A new level replaces any unnumbered entries at the end of the stack.
    opening = len(stack)
    while opening and stack[opening - 1][1] is None:
        opening -= 1
    for kind, (formatter, _) in enumerate(_LABEL_KINDS):
        if kind not in used and formatter(1) == label:
            return opening, kind, 1
    for depth, kind, number in reversed(numbered):
        found = _LABEL_KINDS[kind][1](label)
        if found is not None and found > number:
            _LOGGER.warning(
                'Outline label "%s" skips labels after "%s"', label,
                _LABEL_KINDS[kind][0](number))
            return depth, kind, found
    expected = [
        _LABEL_KINDS[kind][0](number + 1) for _, kind, number in numbered]
    expected.extend(
        formatter(1) for kind, (formatter, _) in enumerate(_LABEL_KINDS)
        if kind not in used)
    message = (
        f'cannot place outline label "{label}" (expected one of: '
        f'{", ".join(expected)})')
    raise ValueError(message)


def _place_unnumbered(
        label: str,
        title: str,
        stack: _Stack) -> tuple[int, int | None, int]:
    """Returns where an unnumbered entry belongs in the outline.

    Args:
        label: the dashes of the entry ('-' for the top level).
        title: the title of the entry, for error messages.
        stack: the open entries, from the top level down to the most recent
            entry, each with the kind and number of the labels at its level.

    Returns:
        The level of the entry and the kind and number of the labels at that
            level, so that numbering continues after the entry.

    Raises:
        ValueError: if the entry would be more than one level below the
            previous entry.

    """
    depth = len(label) - 1
    if depth > len(stack):
        message = (
            f'unnumbered entry "{label}: {title}" is more than one level '
            'below the entry before it')
        raise ValueError(message)
    if depth < len(stack):
        return depth, stack[depth][1], stack[depth][2]
    return depth, None, 0


def _roman(number: int) -> str:
    """Returns the upper case Roman numeral for `number`.

    Args:
        number: a positive number.

    Returns:
        The Roman numeral.

    """
    numeral = ''
    for value, symbol in _ROMAN_NUMERALS:
        count, number = divmod(number, value)
        numeral += symbol * count
    return numeral


_LABEL_KINDS: tuple[
        tuple[Callable[[int], str], Callable[[str], int | None]], ...] = (
    (_roman, _parse_roman),
    (lambda n: _letters(n, string.ascii_uppercase),
     lambda label: _parse_letters(label, string.ascii_uppercase)),
    (str, _parse_number),
    (lambda n: _letters(n, string.ascii_lowercase),
     lambda label: _parse_letters(label, string.ascii_lowercase)),
    (lambda n: _roman(n).lower(),
     lambda label: (
         _parse_roman(label.upper()) if label.islower() else None)))
