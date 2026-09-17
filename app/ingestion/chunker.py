import re


def detect_section(text: str) -> str:
    """
    Attempt to identify the current policy section.
    """

    patterns = [
        r"WHAT WE COVER",
        r"WHAT WE EXCLUDE",
        r"GENERAL CONDITIONS",
        r"DEFINITIONS",
        r"BENEFITS",
        r"EXCLUSIONS",
        r"WAITING PERIOD",
        r"PRE-EXISTING",
        r"CLAIMS",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return match.group(0).strip()

    return "UNKNOWN"


def chunk_pages(
    pages: list[dict],
    chunk_size: int = 1200,
    overlap: int = 200,
) -> list[dict]:

    chunks = []

    for page in pages:
        page_number = page["page"]
        text = page["text"]

        if not text.strip():
            continue

        section = detect_section(text)

        start = 0
        chunk_number = 1

        while start < len(text):

            end = start + chunk_size

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    {
                        "chunk_id": (
                            f"policy_p{page_number}_chunk_{chunk_number:02d}"
                        ),
                        "page": page_number,
                        "section": section,
                        "text": chunk_text,
                        "source": (
                            "USGIC-CSCIndividualHealthInsurance_2017-2018.pdf"
                        ),
                    }
                )

            if end >= len(text):
                break

            start = end - overlap
            chunk_number += 1

    return chunks
if __name__ == "__main__":
    from app.ingestion.loader import load_policy

    pdf_path = (
        "data/policy/"
        "USGIC-CSCIndividualHealthInsurance_2017-2018.pdf"
    )

    pages = load_policy(pdf_path)

    chunks = chunk_pages(pages)

    print(f"Created {len(chunks)} chunks")

    for chunk in chunks[:5]:
        print("\n-----------------------------")
        print("ID:", chunk["chunk_id"])
        print("Page:", chunk["page"])
        print("Section:", chunk["section"])
        print("Text:", chunk["text"][:300])