import logging
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

logger = logging.getLogger(__name__)

DATA_DIR = Path("data/raw")

# Maps filename -> a human-readable topic label.
# We use this instead of the old "pregnancy stage" idea, since none of
# our documents are actually stage-specific — they're topic-specific.
TOPIC_MAP = {
    "nutrition.pdf": "nutrition",
    "mental-wellness.pdf": "mental_wellness",
    "postnatal-baby-care.pdf": "postnatal_baby_care",
    "postnatal-care-who-guidelines.pdf": "postnatal_baby_care",
    "pregnancy-myths-facts.pdf": "myths_facts",
    "medical-fitness-exercise.pdf": "fitness_exercise",
    "vaccination-information.pdf": "vaccination",
    "financial-guidance-pmmvy.pdf": "financial_guidance",
    "hydration-sleep-lifestyle.pdf": "lifestyle",
    "symptom-checker-emergency-signs.pdf": "emergency_signs",
}


@dataclass
class LoadedPage:
    source: str
    topic: str
    page_number: int
    text: str


def clean_text(text: str) -> str:
    """Drop lines that are mostly non-ASCII garbage (e.g. mis-decoded
    Devanagari text in the PMMVY PDF) so it doesn't pollute embeddings."""
    cleaned_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        ascii_chars = sum(1 for c in stripped if c.isascii())
        if ascii_chars / len(stripped) < 0.7:
            continue
        cleaned_lines.append(stripped)
    return "\n".join(cleaned_lines)


def load_all_pdfs() -> list[LoadedPage]:
    pages: list[LoadedPage] = []

    if not DATA_DIR.exists():
        raise FileNotFoundError(f"Expected PDFs in {DATA_DIR}, folder not found")

    pdf_files = sorted(DATA_DIR.glob("*.pdf"))
    if not pdf_files:
        raise ValueError(f"No PDFs found in {DATA_DIR}")

    for pdf_path in pdf_files:
        topic = TOPIC_MAP.get(pdf_path.name, "general")
        reader = PdfReader(str(pdf_path))

        page_count = 0
        for i, page in enumerate(reader.pages, start=1):
            raw_text = page.extract_text() or ""
            text = clean_text(raw_text)
            if not text:
                continue
            pages.append(LoadedPage(source=pdf_path.name, topic=topic, page_number=i, text=text))
            page_count += 1

        logger.info("Loaded %s: %d/%d pages with usable text (topic=%s)",
                    pdf_path.name, page_count, len(reader.pages), topic)

    return pages


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    all_pages = load_all_pdfs()
    total_chars = sum(len(p.text) for p in all_pages)
    print(f"\nTotal pages loaded: {len(all_pages)}")
    print(f"Total characters: {total_chars:,}")