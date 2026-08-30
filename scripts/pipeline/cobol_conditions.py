#!/usr/bin/env python3
"""Boolean conditions as a structure, not as text.

Guard conditions were previously assembled by concatenating strings and then
"balancing" the parentheses by counting them and appending whatever was
missing. Counting cannot recover structure that was never recorded, so the
result could be well-formed by that measure and still meaningless -- one edge
in PDCBVC carried ``(TWCOB-FUNZIONE = 'I'))))))))`` and eight redundant terms.

Here a condition is parsed once into a tree, combined as a tree, and rendered
to text exactly once at the end. Nothing downstream edits condition text.
"""
from __future__ import annotations

import re
from typing import Iterable, List, NamedTuple, Optional, Sequence, Tuple, Union


# Precedence, lowest first. COBOL binds NOT tighter than AND, and AND tighter
# than OR, so a child needs parentheses only when it binds more loosely than
# its parent.
_OR, _AND, _NOT, _ATOM = 1, 2, 3, 4


# NamedTuple rather than dataclass: these modules are loaded in tests through
# importlib.spec_from_file_location without being registered in sys.modules,
# which dataclass field resolution cannot survive.
class Atom(NamedTuple):
    """A relation such as ``WCTRIG GREATER 15``, kept verbatim."""

    text: str

    precedence = _ATOM


class Not(NamedTuple):
    operand: "Expr"

    precedence = _NOT


class And(NamedTuple):
    operands: Tuple["Expr", ...]

    precedence = _AND


class Or(NamedTuple):
    operands: Tuple["Expr", ...]

    precedence = _OR


Expr = Union[Atom, Not, And, Or]


_TOKEN_RE = re.compile(
    r"""
    (?P<lparen>\()
  | (?P<rparen>\))
  | (?P<op>(?<![A-Z0-9-])(?:AND|OR|NOT)(?![A-Z0-9-]))
  | (?P<literal>'[^']*'|"[^"]*")
  | (?P<word>[^\s()]+)
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Relational operators, including the COBOL word forms. Used to tell a complete
# relation from a bare operand in an abbreviated combined relation.
_RELATION_RE = re.compile(
    r"(?<![A-Z0-9-])(?:=|<>|<=|>=|<|>|EQUAL(?:\s+TO)?|EQUALS"
    r"|GREATER(?:\s+THAN)?(?:\s+OR\s+EQUAL(?:\s+TO)?)?"
    r"|LESS(?:\s+THAN)?(?:\s+OR\s+EQUAL(?:\s+TO)?)?)(?![A-Z0-9-])",
    re.IGNORECASE,
)


def _tokenize(text: str) -> List[Tuple[str, str]]:
    tokens: List[Tuple[str, str]] = []
    for match in _TOKEN_RE.finditer(text or ""):
        kind = match.lastgroup or "word"
        tokens.append((kind, match.group()))
    return tokens


class _Parser:
    """Recursive descent over ``or := and (OR and)*`` and so on.

    Unparseable input is never discarded: the parser falls back to keeping the
    remaining text as one atom, because a condition rendered verbatim is honest
    while a silently dropped conjunct is not.
    """

    def __init__(self, tokens: Sequence[Tuple[str, str]]):
        self.tokens = list(tokens)
        self.pos = 0

    def peek(self) -> Optional[Tuple[str, str]]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def parse(self) -> Optional[Expr]:
        expr = self.parse_or()
        return expr

    def parse_or(self) -> Optional[Expr]:
        operands: List[Expr] = []
        first = self.parse_and()
        if first is None:
            return None
        operands.append(first)
        while True:
            token = self.peek()
            if not token or token[0] != "op" or token[1].upper() != "OR":
                break
            self.pos += 1
            nxt = self.parse_and()
            if nxt is None:
                break
            operands.append(nxt)
        operands = _expand_abbreviated(operands)
        return operands[0] if len(operands) == 1 else Or(tuple(operands))

    def parse_and(self) -> Optional[Expr]:
        operands: List[Expr] = []
        first = self.parse_not()
        if first is None:
            return None
        operands.append(first)
        while True:
            token = self.peek()
            if not token or token[0] != "op" or token[1].upper() != "AND":
                break
            self.pos += 1
            nxt = self.parse_not()
            if nxt is None:
                break
            operands.append(nxt)
        operands = _expand_abbreviated(operands)
        return operands[0] if len(operands) == 1 else And(tuple(operands))

    def parse_not(self) -> Optional[Expr]:
        token = self.peek()
        if token and token[0] == "op" and token[1].upper() == "NOT":
            # NOT also appears inside relations ("A NOT = B"), where it belongs
            # to the atom rather than negating an expression. Treat it as a
            # logical NOT only when what follows starts a new expression.
            nxt = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
            if nxt and nxt[0] == "lparen":
                self.pos += 1
                operand = self.parse_not()
                return Not(operand) if operand is not None else None
        return self.parse_primary()

    def parse_primary(self) -> Optional[Expr]:
        token = self.peek()
        if token is None:
            return None
        if token[0] == "lparen":
            self.pos += 1
            inner = self.parse_or()
            token = self.peek()
            if token and token[0] == "rparen":
                self.pos += 1
            return inner
        if token[0] == "rparen":
            return None
        return self.parse_atom()

    def parse_atom(self) -> Optional[Expr]:
        words: List[str] = []
        depth = 0
        while self.pos < len(self.tokens):
            kind, value = self.tokens[self.pos]
            if kind == "op" and value.upper() in {"AND", "OR"} and depth == 0:
                break
            if kind == "rparen":
                if depth == 0:
                    break
                depth -= 1
            elif kind == "lparen":
                depth += 1
            words.append(value)
            self.pos += 1
        text = " ".join(words).strip()
        text = re.sub(r"\s+", " ", text)
        return Atom(text) if text else None


def _expand_abbreviated(operands: List[Expr]) -> List[Expr]:
    """Expand COBOL abbreviated combined relations.

    ``TWCOB-FUNZIONE = 'I' OR 'A'`` means the subject and relational operator
    carry over to the following operands. Left unexpanded, the bare ``'A'``
    reads as a free-standing term and any consumer of the condition sees a
    comparison that is not there.
    """
    if len(operands) < 2:
        return operands
    expanded: List[Expr] = []
    prefix: Optional[str] = None
    for operand in operands:
        if isinstance(operand, Atom):
            match = _RELATION_RE.search(operand.text)
            if match:
                prefix = operand.text[: match.end()].strip()
                expanded.append(operand)
                continue
            if prefix and _is_bare_operand(operand.text):
                expanded.append(Atom(f"{prefix} {operand.text}".strip()))
                continue
        expanded.append(operand)
    return expanded


def _is_bare_operand(text: str) -> bool:
    """A single literal or identifier, with no relational operator of its own."""
    return bool(re.fullmatch(r"'[^']*'|\"[^\"]*\"|[A-Z0-9$#@-]+", text.strip(), re.IGNORECASE))


def parse_condition(text: str) -> Optional[Expr]:
    """Parse COBOL condition text into an expression tree."""
    cleaned = _strip_trailing_operator(re.sub(r"\s+", " ", (text or "").strip()).rstrip(". "))
    if not cleaned:
        return None
    return normalize(_Parser(_tokenize(cleaned)).parse())


def _strip_trailing_operator(text: str) -> str:
    return re.sub(r"(?<![A-Z0-9-])(?:AND|OR)\s*$", "", text, flags=re.IGNORECASE).strip()


def normalize(expr: Optional[Expr]) -> Optional[Expr]:
    """Flatten nested same-kind nodes, drop repeats, and apply absorption.

    Repeats are not cosmetic. The same guard reached twice by different paths
    produced ``NUMFUNZ = '1' OR NUMFUNZ = '6' OR NUMFUNZ = '1' OR NUMFUNZ = '6'``,
    which reads as four conditions on a program that has two.
    """
    if expr is None:
        return None
    if isinstance(expr, Atom):
        return expr if expr.text else None
    if isinstance(expr, Not):
        operand = normalize(expr.operand)
        if operand is None:
            return None
        if isinstance(operand, Not):  # double negation
            return operand.operand
        if isinstance(operand, Atom):
            # Push the negation into the relation so that "NOT (A = B)" and
            # "A NOT = B" have one representation. Without this the same
            # condition compares unequal to itself depending on which form the
            # source happened to use.
            flipped = _negate_atom(operand)
            if flipped is not None:
                return flipped
        return Not(operand)

    kind = type(expr)
    flattened: List[Expr] = []
    for operand in expr.operands:
        normalized = normalize(operand)
        if normalized is None:
            continue
        if isinstance(normalized, kind):
            flattened.extend(normalized.operands)
        else:
            flattened.append(normalized)

    unique: List[Expr] = []
    for operand in flattened:
        if operand not in unique:
            unique.append(operand)

    unique = _absorb(unique, kind)
    if not unique:
        return None
    if len(unique) == 1:
        return unique[0]
    return kind(tuple(unique))


def _absorb(operands: List[Expr], kind: type) -> List[Expr]:
    """``A OR (A AND B)`` is ``A``; ``A AND (A OR B)`` is ``A``."""
    inner = And if kind is Or else Or
    kept: List[Expr] = []
    for operand in operands:
        if isinstance(operand, inner) and any(
            other in operand.operands for other in operands if other is not operand
        ):
            continue
        kept.append(operand)
    return kept


def render(expr: Optional[Expr]) -> str:
    """Render to text, parenthesising only where precedence requires it."""
    if expr is None:
        return ""
    if isinstance(expr, Atom):
        return expr.text
    if isinstance(expr, Not):
        return f"NOT {_wrap(expr.operand, _NOT)}"
    joiner = " AND " if isinstance(expr, And) else " OR "
    return joiner.join(_wrap(operand, expr.precedence) for operand in expr.operands)


def _wrap(expr: Expr, parent_precedence: int) -> str:
    text = render(expr)
    return f"({text})" if expr.precedence < parent_precedence else text


def conjoin(*exprs: Optional[Expr]) -> Optional[Expr]:
    present = [e for e in exprs if e is not None]
    if not present:
        return None
    return normalize(And(tuple(present)))


def disjoin(exprs: Iterable[Optional[Expr]]) -> Optional[Expr]:
    present = [e for e in exprs if e is not None]
    if not present:
        return None
    return normalize(Or(tuple(present)))


# COBOL negates a relation in place ("A NOT = B"), so negating one is the
# removal or insertion of that NOT rather than a wrapper. Keeping the source's
# own form avoids rendering a fallback branch as "NOT WCTPAG NOT GREATER 1".
_NEGATABLE_RELATION_RE = re.compile(
    r"(?<![A-Z0-9-])(?P<not>NOT\s+)?(?P<op>=|<>|<=|>=|<|>"
    r"|EQUAL(?:\s+TO)?|EQUALS"
    r"|GREATER(?:\s+THAN)?(?:\s+OR\s+EQUAL(?:\s+TO)?)?"
    r"|LESS(?:\s+THAN)?(?:\s+OR\s+EQUAL(?:\s+TO)?)?)(?![A-Z0-9-])",
    re.IGNORECASE,
)


def _negate_atom(atom: Atom) -> Optional[Expr]:
    matches = list(_NEGATABLE_RELATION_RE.finditer(atom.text))
    if len(matches) != 1:
        return None
    match = matches[0]
    if match.group("not"):
        flipped = atom.text[: match.start("not")] + atom.text[match.start("op"):]
    else:
        flipped = atom.text[: match.start("op")] + "NOT " + atom.text[match.start("op"):]
    return Atom(re.sub(r"\s+", " ", flipped).strip())


def negate(expr: Optional[Expr]) -> Optional[Expr]:
    if expr is None:
        return None
    if isinstance(expr, Atom):
        flipped = _negate_atom(expr)
        if flipped is not None:
            return flipped
    return normalize(Not(expr))


def condition_text(text: str) -> str:
    """Parse and re-render one condition, the common case for callers."""
    return render(parse_condition(text))
