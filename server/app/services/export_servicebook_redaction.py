# server/app/services/export_servicebook_redaction.py
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional, Set, Tuple

APPROVED_STATUS = "APPROVED"

# Freitextfelder (redacted export: kein Freitext)
_SENSITIVE_TEXT_KEYS = {
    "notes",
    "note",
    "free_text",
    "freeText",
    "internal_notes",
    "internalNotes",
}

# Doc-ID Keys, die wir als "Dokument-Referenz" behandeln
_DOC_ID_KEYS = ("doc_id", "document_id", "documentId", "documentID")

# Keys, die typischerweise Listen von Doc-IDs enthalten
_DOC_ID_LIST_KEYS = ("doc_ids", "document_ids", "documentIds", "documentIDs")

# Keys, die typischerweise Dokument-Objekte oder Refs enthalten
_DOC_OBJECT_LIST_KEYS = ("documents", "document_refs", "documentRefs", "attachments", "attachment_docs")


def _as_str(v: Any) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, str):
        s = v.strip()
        return s if s else None
    try:
        s = str(v).strip()
        return s if s else None
    except Exception:
        return None


def _is_approved_status(status_val: Any) -> bool:
    s = _as_str(status_val)
    return bool(s) and s.upper() == APPROVED_STATUS


def _doc_id_from_obj(doc_obj: Any) -> Optional[str]:
    """
    Extrahiert eine Doc-ID aus einem Dokument-Objekt (dict) oder String.
    """
    if doc_obj is None:
        return None
    if isinstance(doc_obj, str):
        return _as_str(doc_obj)
    if isinstance(doc_obj, dict):
        for k in _DOC_ID_KEYS:
            if k in doc_obj:
                return _as_str(doc_obj.get(k))
    return None


def _scrub_sensitive_text(obj: Any) -> Any:
    """
    Entfernt Freitextfelder rekursiv (deny-by-default bzgl. Freitext).
    """
    if obj is None:
        return None

    if isinstance(obj, dict):
        new_d: Dict[str, Any] = {}
        for k, v in obj.items():
            if k in _SENSITIVE_TEXT_KEYS:
                continue
            new_d[k] = _scrub_sensitive_text(v)
        return new_d

    if isinstance(obj, list):
        return [_scrub_sensitive_text(x) for x in obj]

    return obj


def _collect_allowed_from_doc_list(doc_list: Any) -> Set[str]:
    """
    Allowed Doc-IDs nur aus Objekten mit Status APPROVED.
    (deny-by-default: ohne Status/ID -> nicht erlaubt)
    """
    allowed: Set[str] = set()
    if not isinstance(doc_list, list):
        return allowed

    for d in doc_list:
        if not isinstance(d, dict):
            continue
        doc_id = _doc_id_from_obj(d)
        if not doc_id:
            continue
        if _is_approved_status(d.get("status")):
            allowed.add(doc_id)
    return allowed


def _filter_top_level_documents(export_obj: Dict[str, Any]) -> Tuple[Set[str], Dict[str, Any]]:
    """
    Wenn Top-Level `documents` existiert: filtere auf APPROVED und baue allowed set.
    Wenn es NICHT existiert: allowed bleibt leer (deny-by-default -> keine Doc-Refs rausgeben).
    """
    out = deepcopy(export_obj)
    docs = out.get("documents")
    if not isinstance(docs, list):
        return set(), out

    allowed = _collect_allowed_from_doc_list(docs)

    filtered_docs: List[Dict[str, Any]] = []
    for d in docs:
        if not isinstance(d, dict):
            continue
        doc_id = _doc_id_from_obj(d)
        if doc_id and doc_id in allowed:
            filtered_docs.append(d)

    out["documents"] = filtered_docs
    return allowed, out


def _collect_allowed_from_embedded_docs(entry_row: Dict[str, Any]) -> Set[str]:
    """
    Für Entry-Row (ohne Top-Level documents): erlaube nur Doc-IDs,
    die innerhalb der Row als Dokument-Objekt mit Status APPROVED nachweisbar sind.
    """
    allowed: Set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if "status" in node:
                doc_id = _doc_id_from_obj(node)
                if doc_id and _is_approved_status(node.get("status")):
                    allowed.add(doc_id)
            for v in node.values():
                walk(v)
            return

        if isinstance(node, list):
            for it in node:
                walk(it)
            return

    walk(entry_row)
    return allowed


def _filter_id_list(values: Any, allowed: Set[str]) -> Any:
    if not isinstance(values, list):
        return values
    out_list: List[Any] = []
    for v in values:
        vid = _as_str(v)
        if vid and vid in allowed:
            out_list.append(v)
    return out_list


def _scrub_doc_refs(obj: Any, allowed: Set[str]) -> Any:
    """
    Entfernt/Filtert Dokument-Referenzen rekursiv:
    - doc_id/document_id Felder bleiben nur, wenn allowed
    - doc_ids/document_ids Listen werden gefiltert
    - documents/attachments Listen werden auf allowed gefiltert (Objekte oder Strings)
    Zusätzlich: leere Dicts in Listen werden entfernt (damit kein {} übrig bleibt).
    """
    if obj is None:
        return None

    if isinstance(obj, dict):
        new_d: Dict[str, Any] = {}
        for k, v in obj.items():
            # 1) Single Doc-ID Felder
            if k in _DOC_ID_KEYS:
                vid = _as_str(v)
                if vid and vid in allowed:
                    new_d[k] = v
                continue

            # 2) Listen von Doc-IDs
            if k in _DOC_ID_LIST_KEYS:
                new_d[k] = _filter_id_list(v, allowed)
                continue

            # 3) Listen von Doc-Objekten/Refernzen
            if k in _DOC_OBJECT_LIST_KEYS and isinstance(v, list):
                filtered: List[Any] = []
                for item in v:
                    if isinstance(item, dict):
                        did = _doc_id_from_obj(item)
                        if did and did in allowed:
                            cleaned = _scrub_doc_refs(item, allowed)
                            if not (isinstance(cleaned, dict) and not cleaned):
                                filtered.append(cleaned)
                        continue
                    if isinstance(item, str):
                        did = _as_str(item)
                        if did and did in allowed:
                            filtered.append(item)
                        continue
                new_d[k] = filtered
                continue

            # 4) Default: rekursiv weiter
            new_d[k] = _scrub_doc_refs(v, allowed)
        return new_d

    if isinstance(obj, list):
        out_list: List[Any] = []
        for x in obj:
            cleaned = _scrub_doc_refs(x, allowed)
            # wichtig: {} aus Listen entfernen (Test erwartet kein leeres Dict)
            if isinstance(cleaned, dict) and not cleaned:
                continue
            out_list.append(cleaned)
        return out_list

    return obj


def redact_servicebook_entry_row(entry_row: Dict[str, Any], allowed_doc_ids: Optional[Set[str]] = None) -> Dict[str, Any]:
    """
    Kompatibilität für Router: redacted Entry-Row ausgeben.
    - Entfernt Freitext (`notes`, etc.)
    - Doc-Refs nur, wenn allowed_doc_ids oder embedded APPROVED-Doc-Objekte in der Row
    """
    row = deepcopy(entry_row)
    row = _scrub_sensitive_text(row)

    allowed = allowed_doc_ids if allowed_doc_ids is not None else _collect_allowed_from_embedded_docs(row)
    row = _scrub_doc_refs(row, allowed)
    return row


def redact_servicebook_export(export_obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Redaction-Schritt für Servicebook-Exports:
    - Entfernt Freitext (`notes`, etc.)
    - Top-Level `documents` wird auf APPROVED gefiltert (wenn vorhanden)
    - Alle Doc-Refs im gesamten Export bleiben nur, wenn Doc-ID APPROVED ist
    - Wenn kein Top-Level `documents` existiert: allowed bleibt leer -> keine Doc-Refs raus (deny-by-default)
    """
    out = deepcopy(export_obj)
    out = _scrub_sensitive_text(out)

    allowed, out = _filter_top_level_documents(out)
    out = _scrub_doc_refs(out, allowed)
    return out


# Aliases für bestehende Imports/Backwards compat
export_servicebook_redacted = redact_servicebook_export
redact_export_servicebook = redact_servicebook_export
