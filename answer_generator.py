import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Configure Google Gemini API
# Make sure to set your GEMINI_API_KEY as an environment variable (e.g., in a .env file)
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    print("Error: GEMINI_API_KEY environment variable not set.")
    print("Please set the GEMINI_API_KEY environment variable with your Gemini API key.")
    print("You can do this by creating a .env file in the same directory as this script with the content: GEMINI_API_KEY='YOUR_API_KEY_HERE'")
    exit()

def generate_answer_with_gemini(question_text: str, context_text: str, marks: str) -> str:
    """
    Generates an answer using the Google Gemini API based on the provided question and context.

    Args:
        question_text: The question to be answered.
        context_text: The context relevant to the question.
        marks: marks for the question

    Returns:
        The AI-generated answer as a string, or an error message if generation fails.
    """
    try:
        # # Initialize the GenerativeModel with 'gemini-pro'
        model = genai.GenerativeModel('gemini-2.0-flash')

        # Construct the prompt for the Gemini API
        # We instruct the model to use the context to answer the question.
        prompt = f"Context: {context_text}\n\nQuestion: {question_text}\n\n generate the answer for the question using context for the {marks} Answer:"

        # Generate content using the model
        response = model.generate_content(prompt)

        # Return the text from the response
        return response.text
    except Exception as e:
        print(f"An error occurred during Gemini API call: {e}")
        return "Error: Could not generate answer."

def process_json_files(json_folder: str = "json", output_folder: str = "answers_markdown"):
    """
    Processes all JSON files in the specified input folder.
    For each question in a JSON file, it generates an answer using the Gemini API
    and then creates a Markdown file with the questions and generated answers.

    Args:
        json_folder: The path to the folder containing the input JSON files.
        output_folder: The path to the folder where output Markdown files will be saved.
    """
    # Ensure the input JSON folder exists
    if not os.path.exists(json_folder):
        print(f"Error: The input folder '{json_folder}' does not exist.")
        return

    # Create the output Markdown folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    print(f"Output Markdown files will be saved in: {os.path.abspath(output_folder)}\n")

    # Iterate through all files in the specified JSON folder
    for filename in os.listdir(json_folder):
        # Process only files ending with .json
        if filename.endswith(".json"):
            json_filepath = os.path.join(json_folder, filename)
            # Create the corresponding Markdown filename (e.g., sample.json -> sample.md)
            markdown_filename = os.path.splitext(filename)[0] + ".md"
            markdown_filepath = os.path.join(output_folder, markdown_filename)

            print(f"Processing JSON file: {json_filepath}")

            try:
                with open(json_filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Get the filename from the JSON data, or use the base filename if not present
                file_identifier = data.get('filename', os.path.splitext(filename)[0])

                with open(markdown_filepath, 'w', encoding='utf-8') as md_file:
                    # Write the main heading using the 'filename' from the JSON
                    md_file.write(f"# {file_identifier}\n\n")
                    md_file.write("### Questions and Answers\n\n")

                    questions_array = data.get("Question", [])
                    if not questions_array:
                        md_file.write("No questions found in this JSON file.\n")
                        print(f"No questions found in {json_filepath}")
                        continue

                    # Iterate through each question block in the 'Questions' array
                    for i, q_block in enumerate(questions_array):
                        questions_list = q_block.get("Question", [])
                        context = q_block.get("Context", "")
                        marks = q_block.get("Marks", "(Not provided)") # Default if Marks is missing

                        # Handle cases where 'Question' might be a single string instead of a list, or an empty list
                        if isinstance(questions_list, str):
                            questions_list = [questions_list]
                        elif not isinstance(questions_list, list):
                            questions_list = [] # Ensure it's iterable

                        if not questions_list:
                            print(f"Warning: Question list is empty in block {i+1} of {json_filepath}")
                            continue

                        # Process each individual question within the question block
                        for j, question_text in enumerate(questions_list):
                            # Question numbering starts from 1 for each question block
                            # If there are multiple questions in one block, use 1.1, 1.2, etc.
                            question_number_display = f"{i + 1}.{j + 1}" if len(questions_list) > 1 else str(i + 1)

                            md_file.write(f"### Question No: {question_number_display}\n")
                            # Write the context if it exists
                            if context:
                                md_file.write(f"** ** {context.strip()}\n")

                            md_file.write(f"**Question:** {question_text.strip()}\n")
                            md_file.write(f"**Marks:** {marks.strip()}\n")

                            # Generate the answer using Gemini API
                            answer = generate_answer_with_gemini(question_text.strip(), context.strip(),marks)
                            md_file.write(f"**Answer:** {answer.strip()}\n\n")

                print(f"Successfully generated Markdown file: {markdown_filepath}")

            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from {json_filepath}: {e}")
            except Exception as e:
                print(f"An unexpected error occurred while processing {json_filepath}: {e}")
    print("\nAll specified JSON files have been processed.")

if __name__ == "__main__":

    print("\n--- Starting the JSON file processing and answer generation ---")
    process_json_files()
    print("\n--- Processing complete. Check the 'answers_markdown' folder for your generated Markdown files. ---")
