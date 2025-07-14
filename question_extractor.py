import fitz  # PyMuPDF for PDF reading
import google.generativeai as genai
import os

def extract_text_from_pdf(pdf_path):
    """
    Extracts all text from a PDF file.

    Args:
        pdf_path (str): The path to the PDF file.

    Returns:
        str: The concatenated text content from all pages of the PDF.
             Returns an empty string if the file cannot be opened or has no text.
    """
    text = ""
    try:
        # Open the PDF document
        document = fitz.open(pdf_path)
        # Iterate through each page and extract text
        for page_num in range(document.page_count):
            page = document.load_page(page_num)
            text += page.get_text()
        document.close()
    except FileNotFoundError:
        print(f"Error: PDF file not found at {pdf_path}")
    except Exception as e:
        print(f"An error occurred while reading the PDF: {e}")
    return text

def analyze_text_with_gemini(text_content):
    """
    Sends text content to Gemini AI to extract questions related to sexual harassment
    along with their surrounding context.

    Args:
        text_content (str): The text extracted from the PDF.

    Returns:
        str: The response from Gemini AI containing the identified questions and their context.
             Returns an empty string if the API call fails or no content is found.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        return ""

    genai.configure(api_key=api_key)

    # Initialize the Gemini model
    model = genai.GenerativeModel('gemini-2.0-flash') # Using gemini-2.0-flash as per instructions.

    # Craft a precise prompt for the Gemini AI to include context and number the questions
    prompt = f"""
    You are an expert document analyzer. Your task is to carefully read the provided text, which contains questions.
    Identify and extract ONLY those questions that are directly or Indirectly related to the topic of sexual harassment.
    For each such question, also extract the paragraph or case study text that provides its immediate context.

    Present each identified question and its context as a numbered list. Each item in the list should be formatted as follows:
    [Question Number]. Context: [The relevant paragraph/case study text]
    Question: [The identified question]

    Separate each complete entry (Context and Question) with two blank lines.
    Do not include any other text, explanations, or introductory/concluding remarks.
    If no questions related to sexual harassment are found, respond with "No relevant questions found."

    Here is the text to analyze:

    {text_content}
    """

    try:
        print("Sending content to Gemini AI for analysis...")
        response = model.generate_content(prompt)
        # Check if the response contains content
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        else:
            print("Gemini AI did not return any content.")
            return "No relevant questions found."
    except Exception as e:
        print(f"An error occurred during Gemini API call: {e}")
        return "Error during AI analysis."

def write_questions_to_file(questions_text, output_file_path, mode="a"):
    """
    Writes the extracted questions to a specified text file.

    Args:
        questions_text (str): The text containing the questions.
        output_file_path (str): The path to the output text file.
        mode (str): File open mode ('w' for write/overwrite, 'a' for append).
    """
    try:
        with open(output_file_path, mode, encoding="utf-8") as f:
            f.write(questions_text.strip()) # .strip() to remove leading/trailing whitespace
        print(f"Successfully written questions to {output_file_path} in '{mode}' mode.")
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")

if __name__ == "__main__":
    # Define file paths
    pdf_folder = "question_papers"
    output_file_name = "extracted_question.txt"
    output_file_path = output_file_name # Output extracted_question.txt in the current directory

    # Clear the output file at the beginning to ensure a clean start
    write_questions_to_file("", output_file_path, mode="w")

    # Get all PDF files in the specified folder
    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]

    if not pdf_files:
        print(f"No PDF files found in the folder: {pdf_folder}")
    else:
        print(f"Found {len(pdf_files)} PDF files to process in {pdf_folder}.")
        for i, pdf_file_name in enumerate(pdf_files):
            pdf_path = os.path.join(pdf_folder, pdf_file_name)
            print(f"\n--- Processing {pdf_file_name} ({i+1}/{len(pdf_files)}) ---")

            # Step 1: Extract text from PDF
            print(f"Attempting to extract text from {pdf_path}...")
            pdf_content = extract_text_from_pdf(pdf_path)

            if pdf_content:
                print("PDF text extraction complete. Analyzing with Gemini AI...")
                # Step 2: Analyze text with Gemini AI
                relevant_questions = analyze_text_with_gemini(pdf_content)

                # Step 3: Write extracted questions to a file
                if relevant_questions and relevant_questions.strip() != "No relevant questions found.":
                    # Add a separator before writing if it's not the first file
                    if i > 0:
                        write_questions_to_file("\n\n", output_file_path, mode="a") # Separator between PDFs

                    # Add PDF name header
                    header = f"--- Questions from {pdf_file_name} ---\n"
                    write_questions_to_file(header, output_file_path, mode="a")
                    write_questions_to_file(relevant_questions, output_file_path, mode="a")
                else:
                    print(f"No relevant questions were identified in {pdf_file_name} or an error occurred during analysis.")
            else:
                print(f"Could not extract content from {pdf_file_name}. Skipping analysis for this file.")

        print("\n--- All PDF files processed. Check 'extracted_question.txt' for results. ---")
