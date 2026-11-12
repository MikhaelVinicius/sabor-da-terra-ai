import re


REDACTION_PATTERNS = [
    (
        re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),
        "[CPF_REDACTED]",
    ),
    (
        re.compile(
            r"(?i)(conta\s*(?:corrente)?\s*[:\-]?\s*)"
            r"[\d.\-]+"
        ),
        r"\1[CONTA_REDACTED]",
    ),
    (
        re.compile(
            r"(?i)(ag[eê]ncia\s*[:\-]?\s*)"
            r"[\d.\-]+"
        ),
        r"\1[AGENCIA_REDACTED]",
    ),
    (
        re.compile(
            r"(?im)^(.*(?:pix|chave\s+pix).*)$"
        ),
        "[LINHA_PIX_REDACTED]",
    ),
    (
        re.compile(
            r"\(?\d{2}\)?\s*9?\d{4}[-\s]?\d{4}"
        ),
        "[TELEFONE_REDACTED]",
    ),
]


def redact_sensitive_data(text: str) -> str:
    redacted = text

    for pattern, replacement in REDACTION_PATTERNS:
        redacted = pattern.sub(replacement, redacted)

    return redacted