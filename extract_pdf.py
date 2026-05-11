import PyPDF2
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

reader = PyPDF2.PdfReader(r'TESIS Fabian Torrico.pdf')
print(f'Total pages: {len(reader.pages)}')

with open('thesis_full_text.txt', 'w', encoding='utf-8', errors='replace') as f:
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            f.write(f'\n===== PAGE {i+1} =====\n')
            f.write(text)
    print("Done writing to thesis_full_text.txt")
