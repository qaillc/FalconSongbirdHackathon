import fitz  # PyMuPDF
import docx


"""
def extract_text_from_pdf(pdf_file):
    text = ""
    with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

"""

def extract_text_from_pdf(file):
    pdf_document = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text += page.get_text()
    return text


def extract_text_from_word(doc_file):
    text = ""
    doc = docx.Document(doc_file)
    for para in doc.paragraphs:
        text += para.text
    return text
