"""Zero-dependency helpers for the cairn content contract.

Two pieces live here:

  1. A strict frontmatter parser for a deliberately constrained YAML subset.
     Constraining the subset is a feature, not a shortcut: every instance file
     stays uniform, and adopters can validate a cloned repo with nothing
     installed. When PyYAML is present it is used as a cross-check.

  2. A JSON Schema validator covering the keywords this project's schemas
     actually use. The schema files themselves are standards-compliant, so any
     off-the-shelf validator works too; this exists so CI needs no install.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re

SCHEMA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "schema")

# --------------------------------------------------------------------------
# Frontmatter
# --------------------------------------------------------------------------

class FrontmatterError(Exception):
    pass


_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_INT_RE = re.compile(r"^-?\d+$")


def _scalar(raw: str):
    """Coerce a scalar token. Dates stay strings so schema pattern checks work."""
    s = raw.strip()
    if s == "" or s == "~" or s == "null":
        return None
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False
    if _INT_RE.match(s):
        return int(s)
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [_scalar(part) for part in _split_flow(inner)]
    if "#" in s:
        # Strip trailing comment only when clearly separated.
        cut = s.find(" #")
        if cut > 0:
            s = s[:cut].rstrip()
    return s


def _split_flow(inner: str):
    """Split a flow sequence on commas, respecting quotes."""
    parts, buf, quote = [], [], None
    for ch in inner:
        if quote:
            if ch == quote:
                quote = None
            buf.append(ch)
        elif ch in "\"'":
            quote = ch
            buf.append(ch)
        elif ch == ",":
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf))
    return [p for p in (x.strip() for x in parts) if p != ""]


def _lines(text: str):
    out = []
    for n, raw in enumerate(text.split("\n"), start=1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if "\t" in raw[:indent]:
            raise FrontmatterError(f"line {n}: tab indentation is not permitted")
        out.append((indent, raw.strip(), n))
    return out


def _parse_block(toks, i, indent):
    """Parse a mapping or sequence at the given indent. Returns (value, next_i)."""
    if i >= len(toks):
        return None, i
    if toks[i][1].startswith("- "):
        seq = []
        while i < len(toks) and toks[i][0] == indent and toks[i][1].startswith("- "):
            item_indent, content, _ = toks[i]
            rest = content[2:].strip()
            if ":" in rest and not rest.startswith(("\"", "'")):
                # Inline first key of a mapping item.
                synthetic = [(item_indent + 2, rest, toks[i][2])]
                j = i + 1
                while j < len(toks) and toks[j][0] >= item_indent + 2 and not (
                    toks[j][0] == item_indent and toks[j][1].startswith("- ")
                ):
                    synthetic.append(toks[j])
                    j += 1
                val, _ = _parse_block(synthetic, 0, item_indent + 2)
                seq.append(val)
                i = j
            else:
                seq.append(_scalar(rest))
                i += 1
        return seq, i

    mapping = {}
    while i < len(toks) and toks[i][0] == indent:
        _, content, ln = toks[i]
        if content.startswith("- "):
            break
        if ":" not in content:
            raise FrontmatterError(f"line {ln}: expected 'key: value', got {content!r}")
        key, _, rest = content.partition(":")
        key = key.strip()
        rest = rest.strip()
        if rest in ("|", ">"):
            block, j = [], i + 1
            while j < len(toks) and toks[j][0] > indent:
                block.append(toks[j][1])
                j += 1
            sep = "\n" if rest == "|" else " "
            mapping[key] = sep.join(block)
            i = j
        elif rest == "":
            if i + 1 < len(toks) and toks[i + 1][0] > indent:
                child_indent = toks[i + 1][0]
                val, j = _parse_block(toks, i + 1, child_indent)
                mapping[key] = val
                i = j
            else:
                mapping[key] = None
                i += 1
        else:
            mapping[key] = _scalar(rest)
            i += 1
    return mapping, i


def parse_frontmatter(text: str):
    """Split a markdown file into (frontmatter dict, body string)."""
    if not text.startswith("---"):
        raise FrontmatterError("file must open with a '---' frontmatter fence")
    end = text.find("\n---", 3)
    if end == -1:
        raise FrontmatterError("unterminated frontmatter block")
    raw = text[text.find("\n", 3) + 1 : end]
    body = text[end + 4 :].lstrip("\n")
    toks = _lines(raw)
    data, consumed = _parse_block(toks, 0, toks[0][0] if toks else 0)
    if consumed != len(toks):
        raise FrontmatterError(
            f"frontmatter indentation is inconsistent near line {toks[consumed][2]}"
        )
    _crosscheck(raw, data)
    return (data or {}), body


def _crosscheck(raw: str, parsed):
    """If PyYAML is installed, confirm the strict parser agrees with it."""
    try:
        import yaml  # type: ignore
    except ImportError:
        return
    try:
        reference = yaml.safe_load(raw)
    except Exception:
        return
    if _normalise(reference) != _normalise(parsed):
        raise FrontmatterError(
            "frontmatter uses YAML outside the supported subset "
            "(strict parser and PyYAML disagree); simplify the structure"
        )


def _normalise(v):
    if isinstance(v, dict):
        return {str(k): _normalise(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_normalise(x) for x in v]
    if isinstance(v, (_dt.date, _dt.datetime)):
        return v.isoformat()[:10]
    return v


# --------------------------------------------------------------------------
# JSON Schema (subset)
# --------------------------------------------------------------------------

_schema_cache: dict = {}


def load_schema(name: str) -> dict:
    if name not in _schema_cache:
        with open(os.path.join(SCHEMA_DIR, name), encoding="utf-8") as fh:
            _schema_cache[name] = json.load(fh)
    return _schema_cache[name]


def _resolve(ref: str, current: dict) -> dict:
    file_part, _, frag = ref.partition("#")
    doc = load_schema(file_part) if file_part else current
    node = doc
    for part in [p for p in frag.split("/") if p]:
        node = node[part.replace("~1", "/").replace("~0", "~")]
    return node


_TYPES = {
    "object": dict, "array": list, "string": str,
    "integer": int, "number": (int, float), "boolean": bool, "null": type(None),
}


def validate(data, schema: dict, path: str = "", root: dict | None = None):
    """Return a list of human-readable error strings."""
    root = root or schema
    errs: list[str] = []
    if "$ref" in schema:
        return validate(data, _resolve(schema["$ref"], root), path, root)

    if "oneOf" in schema:
        if not any(not validate(data, s, path, root) for s in schema["oneOf"]):
            errs.append(f"{path or 'value'}: does not match any permitted form")
        return errs

    t = schema.get("type")
    if t:
        expected = _TYPES.get(t)
        # bool is a subclass of int in Python; keep them distinct.
        if t == "integer" and isinstance(data, bool):
            errs.append(f"{path or 'value'}: expected integer, got boolean")
            return errs
        if expected and not isinstance(data, expected):
            got = type(data).__name__
            errs.append(f"{path or 'value'}: expected {t}, got {got}")
            return errs

    if "enum" in schema and data not in schema["enum"]:
        errs.append(
            f"{path or 'value'}: {data!r} is not one of {schema['enum']}"
        )
    if isinstance(data, str):
        if "pattern" in schema and not re.match(schema["pattern"], data):
            errs.append(f"{path}: {data!r} does not match {schema['pattern']}")
        if "minLength" in schema and len(data) < schema["minLength"]:
            errs.append(f"{path}: shorter than {schema['minLength']} characters")
        if "maxLength" in schema and len(data) > schema["maxLength"]:
            errs.append(f"{path}: longer than {schema['maxLength']} characters")
        if schema.get("format") == "date" and not _DATE_RE.match(data):
            errs.append(f"{path}: {data!r} is not an ISO date (YYYY-MM-DD)")
    if isinstance(data, (int, float)) and not isinstance(data, bool):
        if "minimum" in schema and data < schema["minimum"]:
            errs.append(f"{path}: below minimum {schema['minimum']}")
        if "maximum" in schema and data > schema["maximum"]:
            errs.append(f"{path}: above maximum {schema['maximum']}")
    if isinstance(data, list):
        if "minItems" in schema and len(data) < schema["minItems"]:
            errs.append(f"{path}: needs at least {schema['minItems']} item(s)")
        if "items" in schema:
            for n, item in enumerate(data):
                errs += validate(item, schema["items"], f"{path}[{n}]", root)
    if isinstance(data, dict):
        props = schema.get("properties", {})
        for req in schema.get("required", []):
            if data.get(req) is None:
                errs.append(f"{path or 'root'}: missing required field '{req}'")
        extra = schema.get("additionalProperties", True)
        for key, val in data.items():
            child = f"{path}.{key}" if path else key
            if key in props:
                errs += validate(val, props[key], child, root)
            elif isinstance(extra, dict):
                errs += validate(val, extra, child, root)
            elif extra is False:
                errs.append(f"{child}: unrecognised field")
    return errs


# --------------------------------------------------------------------------
# Small shared utilities
# --------------------------------------------------------------------------

def today() -> _dt.date:
    override = os.environ.get("CI_TODAY")
    if override:
        return _dt.date.fromisoformat(override)
    return _dt.date.today()


def as_date(value: str) -> _dt.date:
    return _dt.date.fromisoformat(str(value)[:10])


def age_days(value: str) -> int:
    return (today() - as_date(value)).days


def read_text(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def load_doc(path: str):
    return parse_frontmatter(read_text(path))
