import os
import markdown
from xhtml2pdf import pisa  # Import the pisa module for PDF generation
import re # Import regex module for case-insensitive replacement

def convert_markdown_to_pdf(markdown_folder='markdown', pdf_folder='pdf'):
    """
    Converts all Markdown files in the specified markdown_folder to PDF files
    and saves them in the pdf_folder.

    Args:
        markdown_folder (str): The path to the folder containing Markdown files.
        pdf_folder (str): The path to the folder where PDF files will be saved.
    """
    # Create the PDF output directory if it doesn't exist
    if not os.path.exists(pdf_folder):
        os.makedirs(pdf_folder)
        print(f"Created output directory: {pdf_folder}")

    # Iterate over all files in the markdown folder
    for filename in os.listdir(markdown_folder):
        # Check if the file is a Markdown file
        if filename.endswith(('.md', '.markdown')):
            markdown_filepath = os.path.join(markdown_folder, filename)
            # Define the output PDF filename
            pdf_filename = os.path.splitext(filename)[0] + '.pdf'
            pdf_filepath = os.path.join(pdf_folder, pdf_filename)

            print(f"Processing '{filename}'...")

            try:
                # Read the Markdown content
                with open(markdown_filepath, 'r', encoding='utf-8') as md_file:
                    markdown_content = md_file.read()

                # Convert Markdown to HTML
                html_content = markdown.markdown(markdown_content)

                # --- UPDATED LOGIC: "answer" (case-insensitive), "Marks" (case-sensitive) on new line ---
                # Use regex to find and replace "answer" case-insensitively
                html_content = re.sub(r'(answer)', lambda m: '<br/>' + m.group(0), html_content, flags=re.IGNORECASE)
                # Use regex to find and replace "Marks" case-sensitively
                html_content = re.sub(r'(Marks)', lambda m: '<br/>' + m.group(0), html_content) # Removed re.IGNORECASE flag
                # ---------------------------------------------------------------------------------------

                # Create a file object for the PDF output
                with open(pdf_filepath, "wb") as pdf_file:
                    # Convert HTML to PDF
                    pisa_status = pisa.CreatePDF(
                        html_content,    # the HTML to convert
                        dest=pdf_file)   # file handle to receive result

                if not pisa_status.err:
                    print(f"Successfully converted '{filename}' to '{pdf_filename}'")
                else:
                    print(f"Error converting '{filename}': {pisa_status.err}")

            except FileNotFoundError:
                print(f"Error: Markdown file not found at '{markdown_filepath}'")
            except Exception as e:
                print(f"An unexpected error occurred while processing '{filename}': {e}")
        else:
            print(f"Skipping non-Markdown file: {filename}")

    print("\nConversion process completed.")

if __name__ == "__main__":

    convert_markdown_to_pdf(markdown_folder='answers_markdown', pdf_folder='generated_pdf')
