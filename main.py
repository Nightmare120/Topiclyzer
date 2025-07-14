from question_extractor import question_extractor
from answer_generator import process_json_files
from markdown_convertor import convert_markdown_to_pdf

question_extractor()
process_json_files()
convert_markdown_to_pdf(markdown_folder='answers_markdown', pdf_folder='generated_pdf')
