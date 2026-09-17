from pathlib import Path
from pypdf import PdfReader
def load_policy(pdf_path: str) -> list[dict]:
    """
    Extract text from the policy PDF page by page.

    Returns:
        [
            {
                "page": 1,
                "text": "..."
            },
            ...
        ]
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"Policy PDF not found: {path}")
    reader = PdfReader(str(path))
    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        # Basic whitespace cleanup
        text = " ".join(text.split())
        if text.strip():
            pages.append(
                {
                    "page": page_number,
                    "text": text,
                }
            )
    return pages
if __name__ == "__main__":
    pdf_path = "data/policy/USGIC-CSCIndividualHealthInsurance_2017-2018.pdf"
    pages = load_policy(pdf_path)
    print(f"Loaded {len(pages)} pages")
    for page in pages[:3]:
        print(f"\n--- Page {page['page']} ---")
        print(page["text"][:500])