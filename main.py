import io
import os
import re

import fitz
import pytesseract
from PIL import Image


def is_valid_uci(uci: str) -> bool:
    if not isinstance(uci, str) or len(uci) != 13:
        return False

    # Check pattern matches i.e. five digits, one letter or digit, six digits then a check digit.
    pattern = re.compile(r"^\d{5}[A-Z0-9]\d{6}[A-HK-MRTVWXY]$")
    if not pattern.match(uci):
        return False

    core_uci = uci[:12]
    check_digit_provided = uci[12]

    alpha_map = {
        'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9,
        'J': 10, 'K': 11, 'L': 12, 'M': 13, 'N': 14, 'O': 15, 'P': 16, 'Q': 10,
        'R': 11, 'S': 12, 'T': 13, 'U': 14, 'V': 15, 'W': 16, 'X': 10, 'Y': 11, 'Z': 12
    }

    check_digit_map = "ABCDEFGHKLMRTVWXY"

    multipliers = [16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5]

    total_sum = 0
    try:
        for i, char in enumerate(core_uci):
            value = 0
            if i == 5 and char.isalpha():
                value = alpha_map[char]
            else:
                value = int(char)

            total_sum += value * multipliers[i]
    except (KeyError, ValueError):
        return False

    remainder = total_sum % 17
    calculated_check_digit = check_digit_map[remainder]

    return calculated_check_digit == check_digit_provided.upper()

def extract_uci(page_text):
    # Define regex pattern to find all thirteen-character alphanumeric sequences
    uci_pattern = re.compile(r"\b[A-Z0-9]{13}\b")

    # Find all potential UCIs in the page text
    potential_UCIs = uci_pattern.findall(page_text)

    validated_uci = ""
    for uci in potential_UCIs:
        if is_valid_uci(uci):
            validated_uci = uci
            break

    return validated_uci if validated_uci else None


def main():
    input_PDF = 'OCR Statement_Of_Marks_20240814.pdf'
    exam_board = 'OCR'
    output_dir = 'output_pdfs'
    split_pdf_by_uci(input_PDF, output_dir, exam_board)

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts text using PyMuPDF (fitz).
    :param pdf_path:
    :return:
    """
    full_text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for i, page in enumerate(doc):
                full_text += page.get_text() + "\n"
                if i == 5:
                    break
    except Exception as e:
        print(f"Error reading PDF file {pdf_path} with PyMuPDF: {e}")
        return ""
    return full_text

def extract_text_from_pdf_ocr(pdf_path: str) -> str:
    """
    Extracts text from a PDF using OCR with Tesseract.
    :param pdf_path:
    :return:
    """
    full_text = ""
    try:
        doc = fitz.open(pdf_path)
        for i, page in enumerate(doc):
            # Convert page to image
            pix = page.get_pixmap(dpi=300)
            img_data = pix.tobytes("png")
            # Use PIL to open the image and pytesseract to extract text
            image = Image.open(io.BytesIO(img_data))
            page_text = pytesseract.image_to_string(image, lang='eng')
            if page_text:
                # Clean up the text
                full_text += page_text + "\n"
            if i == 5:
                break
        doc.close()
    except pytesseract.TesseractNotFoundError:
        print(f'Tessaract OCR engine not found.')
        return ""
    except Exception as e:
        print(f"An error occurred during OCR processing: {e}")
        return ""
    return full_text

def split_pdf_by_uci(pdf_path, output_dir, exam_board):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with fitz.open(pdf_path) as doc:
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=300)
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))
            page_text = pytesseract.image_to_string(image, lang='eng')
            extracted_uci = extract_uci(page_text)

            if extracted_uci:
                new_pdf = fitz.open()
                new_pdf.insert_pdf(doc, from_page=i, to_page=i)
                output_path = os.path.join(output_dir, f'{extracted_uci}_{exam_board}.pdf')
                new_pdf.save(output_path)
                new_pdf.close()
                print(f'{extracted_uci} extracted - page {i}')



if __name__ == '__main__':
    main()