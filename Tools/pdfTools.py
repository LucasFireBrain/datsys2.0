import sys                  # CLI arguments (Unity: Main(string[] args))
import os                   # Cross-platform path utilities
from pypdf import PdfReader, PdfWriter  # Read-only vs write-only PDF APIs


def merge_pdfs(pdf_paths):
    # Guard clause: require at least 2 PDFs
    if len(pdf_paths) < 2:
        raise ValueError("Provide at least two PDF files.")

    writer = PdfWriter()    # Accumulator object (think combined mesh)

    for path in pdf_paths:  # foreach path in args
        if not os.path.isfile(path):
            raise FileNotFoundError(f"File not found: {path}")

        reader = PdfReader(path)  # Lazy-load PDF

        for page in reader.pages:    # Iterate pages like a list
            writer.add_page(page)    # Append page to output

    first_pdf = pdf_paths[0]  # First file defines output location/name

    base_dir = os.path.dirname(first_pdf)                     # Folder path
    base_name = os.path.splitext(os.path.basename(first_pdf))[0]  # Filename w/o .pdf

    output_path = os.path.join(base_dir, f"{base_name}_MERGED.pdf")

    # Context manager = auto close (Unity: using {})
    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"Merged PDF created at:\n{output_path}")


# Entry-point guard (prevents execution on import)
if __name__ == "__main__":
    pdfs = sys.argv[1:]   # Skip script name
    merge_pdfs(pdfs)
