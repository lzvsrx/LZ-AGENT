from pathlib import Path

import pymupdf

PDF = Path(r"C:\Users\valen\Downloads\LZ_AGENT_DOCUMENTO_MESTRE_COMPLETO_2026.pdf")
OUT = Path(r"C:\LZAGENTE\.spec-extract")
IMAGES = OUT / "images"

OUT.mkdir(parents=True, exist_ok=True)
IMAGES.mkdir(parents=True, exist_ok=True)

document = pymupdf.open(PDF)
chunks = []
image_rows = []

for page_index, page in enumerate(document):
    page_number = page_index + 1
    chunks.append(f"\n\n===== PAGE {page_number} =====\n\n{page.get_text('text')}")
    for image_index, image in enumerate(page.get_images(full=True), start=1):
        xref = image[0]
        payload = document.extract_image(xref)
        filename = f"page-{page_number:04d}-image-{image_index:03d}.{payload['ext']}"
        (IMAGES / filename).write_bytes(payload["image"])
        image_rows.append(
            f"{page_number}\t{image_index}\t{xref}\t{filename}\t{len(payload['image'])}"
        )

(OUT / "document.txt").write_text("".join(chunks), encoding="utf-8")
(OUT / "images.tsv").write_text(
    "page\tindex\txref\tfilename\tbytes\n" + "\n".join(image_rows), encoding="utf-8"
)
print(f"pages={len(document)} images={len(image_rows)} output={OUT}")
