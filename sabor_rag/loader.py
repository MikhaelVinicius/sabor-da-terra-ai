import re
from pathlib import Path

from pypdf import PdfReader

from sabor_rag.config import settings
from sabor_rag.models import SourceDocument
from sabor_rag.redaction import redact_sensitive_data


SUPPORTED_EXTENSIONS = {".txt", ".pdf"}


def _read_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_pdf(path: Path) -> str:
    reader = PdfReader(path)

    pages = []

    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)

    return "\n".join(pages)


def _read_document(path: Path) -> str:
    extension = path.suffix.lower()

    if extension == ".txt":
        return _read_txt(path)

    if extension == ".pdf":
        return _read_pdf(path)

    raise ValueError(
        f"Formato de arquivo não suportado: {extension}"
    )


def _extract_producer_id(
    text: str,
    filename: str,
) -> str | None:
    pattern = r"(?<![A-Za-z0-9])P\d{3}(?!\d)"

    match = re.search(
        pattern,
        filename,
        re.IGNORECASE,
    )

    if match:
        return match.group(0).upper()

    match = re.search(
        pattern,
        text,
        re.IGNORECASE,
    )

    if match:
        return match.group(0).upper()

    return None


def _extract_dates(text: str) -> list[str]:
    return re.findall(
        r"\b\d{2}/\d{2}/\d{4}\b",
        text,
    )


def _build_metadata(
    path: Path,
    category: str,
    text: str,
) -> dict:
    metadata = {
        "filename": path.name,
        "category": category,
    }

    producer_id = _extract_producer_id(
        text,
        path.name,
    )

    if producer_id:
        metadata["producer_id"] = producer_id

    dates = _extract_dates(text)

    if dates:
        metadata["dates"] = dates

    return metadata


def load_document(
    path: Path,
    docs_dir: Path,
) -> SourceDocument:
    raw_text = _read_document(path)

    category = path.parent.name

    metadata = _build_metadata(
        path=path,
        category=category,
        text=raw_text,
    )

    text = raw_text

    if settings.redact_sensitive:
        text = redact_sensitive_data(text)

    relative_path = path.relative_to(docs_dir)

    document_id = relative_path.with_suffix("").as_posix()

    return SourceDocument(
        document_id=document_id,
        text=text,
        source_path=relative_path.as_posix(),
        category=category,
        metadata=metadata,
    )


def load_documents(
    docs_dir: Path | None = None,
) -> list[SourceDocument]:
    base_dir = docs_dir or settings.docs_dir

    if not base_dir.exists():
        raise FileNotFoundError(
            f"Diretório de documentos não encontrado: {base_dir}"
        )

    paths = sorted(
        path
        for path in base_dir.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    documents = [
        load_document(path, base_dir)
        for path in paths
    ]

    return documents