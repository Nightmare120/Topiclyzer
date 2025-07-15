import re
import fitz  # PyMuPDF for PDF reading
import google.generativeai as genai
import os
import json

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

def analyze_text_with_gemini(text_content, pdf_file_name,topic_to_find):
    """
    Sends text content to Gemini AI to extract questions related to topic_to_find
    along with their surrounding context.

    Args:
        text_content (str): The text extracted from the PDF.
        pdf_file_name (str): pdf file name.
        topic_to_find (str): topic to find in pdf.

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
    Identify and extract ONLY those questions that are directly related to the topic of {topic_to_find}.
    For each such question, also extract the paragraph or case study text that provides its immediate context.

    Present each identified question as a JSON object with the following structure:
    {{
        "Question": Array of Identified Question with same context"[The identified question]",
        "Context": "[The relevant paragraph/case study text]",
        "Marks": "[Marks if available in the pdf]"
    }} 
    Context: [The relevant paragraph/case study text]
    Question: [The identified question] Marks: [Marks if available in the pdf]

    if no context was with the question then you can leave the context empty and If their was two question with same context then you shouldn't write context two times, just add the question in the array of questions.
    
    In the end return the JSON array of all identified questions and their contexts. like this 
    {{"filename":{pdf_file_name},
    "Question": then the above questin block in this list
    }}

    Dont write JSON in the start and end of the response, just return the JSON array of all identified questions and their contexts.
    Dont write triple backtick strings, I dont want markdown formatting.
    Do not include any other text, explanations, or introductory/concluding remarks.
    If no questions related to {topic_to_find} are found, respond with "No relevant questions found."

    Here is the text to analyze:

    {text_content}
    """

    try:
        print("Sending content to Gemini AI for analysis...")
        response = model.generate_content(prompt)
        # Check if the response contains content
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            return extract_json_from_response(response.candidates[0].content.parts[0].text)
        else:
            print("Gemini AI did not return any content.")
            return "No relevant questions found."
    except Exception as e:
        print(f"An error occurred during Gemini API call: {e}")
        return "Error during AI analysis."

def write_questions_to_file(data, json_file_name):
    """
    Writes the extracted questions to a specified text file.

    Args:
        data (str): The text containing the questions.
        json_file_name (str): The path to the output text file.
    """
    
    try:
            with open(f"json/{json_file_name}", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
            print(f"Failed to write JSON to file: {e}")

def extract_json_from_response(response_text):
    """
    Extracts JSON from a code block string like:
    ```json
    {...}
    ```
    """
    # Match anything between triple backticks
    match = re.search(r"```(?:json)?\s*(.*?)```", response_text, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
        return json.loads(json_str)
    else:
        raise ValueError("No JSON code block found in the response.")
    
def question_extractor():
    # Asking for file paths from the User
    pdf_folder = input("Enter the path to the folder containing PDF files (default: question_papers/): ").strip() or "question_papers"
    # output_file_name = input("Enter the name of the output file (default: extracted_question.txt): ").strip() or "extracted_question.txt"
    # output_file_path = output_file_name # Output extracted_question.txt in the current directory

    # Get all PDF files in the specified folder
    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]

    topic_to_find = input("Enter the topic to find: ").strip() or "sexual harassment"
    
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
                relevant_questions = analyze_text_with_gemini(pdf_content, pdf_file_name,topic_to_find)
    
                # Step 3: Write extracted questions to a file
                if relevant_questions and relevant_questions != "No relevant questions found." and relevant_questions != "Error during AI analysis.":
                    newPath = pdf_file_name.replace(".pdf", ".json")
                    write_questions_to_file(relevant_questions, newPath)
                    print(f"Relevant questions from {pdf_file_name} have been written to {newPath}.")
                else:
                    print(f"No relevant questions were identified in {pdf_file_name} or an error occurred during analysis.")
   
            else:
                print(f"Could not extract content from {pdf_file_name}. Skipping analysis for this file.")

        print("\n--- All PDF files processed ---")

if __name__ == "__main__":
    question_extractor()
    