"""Shared document processing for Mate's RAG pipeline.

Handles PDF text extraction, table extraction, heading-aware chunking,
and retrieval re-ranking — used by both doc_qa and construction_assistant.
"""

import re
from datetime import datetime, timezone

import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter


# --- Chunking defaults (tuned for construction documents) ---

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

# --- Retrieval defaults ---

RELEVANCE_THRESHOLD = 1.5
MAX_CHUNKS_PER_PAGE = 3
MAX_TOTAL_CHUNKS = 6

# --- Heading detection ---

# Matches "Clause 2.3", "Section 4", "Part A", "Schedule 1", "Article 3.1"
KEYWORD_HEADING = re.compile(
    r"^(?:clause|section|part|schedule|appendix|article)\s*"
    r"(\d+(?:\.\d+)*)"
    r"[\s:.\-]",
    re.IGNORECASE,
)

# Matches "2.3.1 Some title" or "1. Introduction"
STANDARD_NUMBERED = re.compile(r"^(\d+(?:\.\d+)*)\s+[A-Z]")

# Matches ALL CAPS headers like "PRELIMINARIES" or "GENERAL REQUIREMENTS"
ALL_CAPS_HEADING = re.compile(r"^[A-Z][A-Z\s&/,\-]{4,}$")


def detect_heading(line: str) -> str | None:
    """Return the heading text if this line looks like a heading, else None."""
    line = line.strip()
    if not line:
        return None
    for pattern in (KEYWORD_HEADING, STANDARD_NUMBERED):
        m = pattern.match(line)
        if m:
            return line[:120]
    if ALL_CAPS_HEADING.match(line):
        return line[:120]
    return None


def extract_pages(path: str) -> list[dict]:
    """Extract text and tables from each page of a PDF.

    Returns a list of dicts, one per non-blank page:
        {"page": int, "text": str, "tables": list[str]}
    Tables are formatted as markdown strings.
    """
    pdf = fitz.open(path)
    pages = []
    for page_number, page in enumerate(pdf, start=1):
        page_text = page.get_text()
        tables_md = []
        try:
            for table in page.find_tables():
                rows = table.extract()
                if rows and len(rows) >= 2:
                    md = _format_table(rows)
                    if md:
                        tables_md.append(md)
        except Exception:
            pass  # table extraction is best-effort
        if page_text.strip() or tables_md:
            pages.append({"page": page_number, "text": page_text, "tables": tables_md})
    pdf.close()
    return pages


def _format_table(rows: list[list[str | None]]) -> str:
    """Convert extracted table rows into a markdown table string."""
    cleaned = [[str(cell or "").strip() for cell in row] for row in rows]
    if not cleaned:
        return ""
    header = cleaned[0]
    sep = ["---"] * len(header)
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(sep) + " |",
    ]
    for row in cleaned[1:]:
        padded = row + [""] * max(0, len(header) - len(row))
        lines.append("| " + " | ".join(padded[: len(header)]) + " |")
    return "\n".join(lines)


def _heading_prefix(headings: list[str]) -> str:
    """Build a context prefix from the current heading stack."""
    if not headings:
        return ""
    return "[" + " > ".join(headings[-3:]) + "]\n"


def chunk_pages(
    pages: list[dict],
    doc_id: str,
    filename: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> tuple[list[str], list[dict]]:
    """Split extracted pages into heading-aware chunks with metadata.

    Returns (documents, metadatas) ready for ChromaDB's .add().
    Heading context is tracked across pages and prepended to every chunk
    that falls under a detected heading.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    all_chunks: list[str] = []
    all_metadatas: list[dict] = []
    current_headings: list[str] = []

    for page_data in pages:
        page_text = page_data["text"]
        page_number = page_data["page"]

        # --- Table chunks (even if page text is empty) ---
        for table_md in page_data.get("tables", []):
            if table_md.strip():
                prefix = _heading_prefix(current_headings)
                all_chunks.append(prefix + table_md)
                all_metadatas.append({
                    "doc_id": doc_id,
                    "filename": filename,
                    "page": page_number,
                    "chunk_type": "table",
                    "uploaded_at": datetime.now(timezone.utc).isoformat(),
                })

        if not page_text.strip():
            continue

        # --- Section-based splitting with heading tracking ---
        lines = page_text.split("\n")
        sections: list[tuple[str, str]] = []  # (heading_prefix, raw_text)
        section_lines: list[str] = []
        section_headings = list(current_headings)

        for line in lines:
            heading = detect_heading(line)
            if heading:
                # Flush previous section
                if section_lines:
                    raw = "\n".join(section_lines)
                    if raw.strip():
                        sections.append((_heading_prefix(section_headings), raw))
                section_headings = (section_headings[-2:] + [heading])[-3:]
                section_lines = [line]
            else:
                section_lines.append(line)

        # Flush last section
        if section_lines:
            raw = "\n".join(section_lines)
            if raw.strip():
                sections.append((_heading_prefix(section_headings), raw))

        # Carry the last heading state forward for subsequent pages
        current_headings = list(section_headings)

        # Split each section, then prepend heading context to every chunk
        for prefix, raw_text in sections:
            chunks = splitter.split_text(raw_text)
            for chunk in chunks:
                all_chunks.append(prefix + chunk)
                all_metadatas.append({
                    "doc_id": doc_id,
                    "filename": filename,
                    "page": page_number,
                    "chunk_type": "text",
                    "uploaded_at": datetime.now(timezone.utc).isoformat(),
                })

    return all_chunks, all_metadatas


def rerank_chunks(
    chunks: list[str],
    distances: list[float],
    metadatas: list[dict],
    max_per_page: int = MAX_CHUNKS_PER_PAGE,
    max_total: int = MAX_TOTAL_CHUNKS,
    threshold: float = RELEVANCE_THRESHOLD,
) -> tuple[list[str], list[dict]]:
    """Filter and diversify retrieved chunks.

    Ensures no single page dominates results, applies relevance threshold,
    and returns up to *max_total* chunks ordered by distance (ascending).

    Returns (filtered_chunks, filtered_metadatas).
    """
    page_counts: dict[tuple, int] = {}
    selected_chunks: list[str] = []
    selected_metadatas: list[dict] = []

    for chunk, distance, meta in zip(chunks, distances, metadatas):
        if distance > threshold:
            continue
        page_key = (meta.get("filename", ""), meta.get("page", 0))
        if page_counts.get(page_key, 0) >= max_per_page:
            continue
        page_counts[page_key] = page_counts.get(page_key, 0) + 1
        selected_chunks.append(chunk)
        selected_metadatas.append(meta)
        if len(selected_chunks) >= max_total:
            break

    return selected_chunks, selected_metadatas
