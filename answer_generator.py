import json
import os
import re
import asyncio
import aiohttp

async def generate_answer_with_gemini(full_question_text: str, api_key: str) -> str:
    """
    Generates a detailed and comprehensive answer for a given combined question text
    (including its context) using the Gemini API.
    """
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    # The full_question_text already contains the context and the specific question.
    # We instruct Gemini to provide a detailed answer (at least 300 words) based on this combined input.
    prompt_for_gemini = (
        f"Please provide a detailed and comprehensive answer, at least 300 words long, "
        f"based on the following text. Focus on directly answering the question presented within the text "
        f"while elaborating on all relevant details from the context.\n\n"
        f"{full_question_text}\n\n"
        f"Answer:"
    )

    chat_history = [{ "role": "user", "parts": [{ "text": prompt_for_gemini }] }]

    payload = {
        "contents": chat_history
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=payload, headers={'Content-Type': 'application/json'}) as response:
                response.raise_for_status() # Raise an exception for HTTP errors
                result = await response.json()

                if result.get("candidates") and result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts"):
                    return result["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    print(f"Warning: Unexpected response structure for input: {full_question_text[:100]}...")
                    return "Could not generate an answer due to unexpected API response."
    except aiohttp.ClientError as e:
        print(f"Error calling Gemini API: {e}")
        return f"Error: Failed to connect to Gemini API. {e}"
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return f"Error: An unexpected error occurred. {e}"

async def main():
    input_file = "extracted_question.txt"
    output_file = "output.json"
    
    # List to store dictionaries of {"full_question_text": ...}
    parsed_questions = [] 
    output_data = [] # List to store final output: {"question": ..., "answer": ...}

    # Attempt to get API key from environment variable
    api_key = os.getenv("GEMINI_API_KEY", "")

    if not api_key:
        print("Warning: GEMINI_API_KEY environment variable not set.")
        print("Please set the GEMINI_API_KEY environment variable or hardcode your API key in the script.")
        return

    # Variables for parsing the input file
    current_question_block_lines = []
    
    # Read questions and their contexts from the input file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            i = 0
            while i < len(lines):
                stripped_line = lines[i].strip()

                # If we encounter a file header or a new context, it marks the start of a new question block
                if stripped_line.startswith("--- Questions from") or stripped_line.startswith("Context:"):
                    # If there was a previous block, save it
                    if current_question_block_lines:
                        # Filter out the "--- Questions from" lines before joining
                        filtered_block = [
                            line for line in current_question_block_lines 
                            if not line.startswith("--- Questions from")
                        ]
                        parsed_questions.append("\n".join(filtered_block).strip())
                        current_question_block_lines = [] # Reset for the new block
                    
                    # Add the current line (Context: or --- Questions from) to the new block
                    current_question_block_lines.append(lines[i].strip())
                    i += 1
                    
                    # Continue adding lines until the next "Context:", "--- Questions from", or end of file
                    while i < len(lines) and not (lines[i].strip().startswith("--- Questions from") or lines[i].strip().startswith("Context:")):
                        current_question_block_lines.append(lines[i].strip())
                        i += 1
                else:
                    i += 1 # Move to next line if not a start of a block

            # Add the last block if it exists
            if current_question_block_lines:
                # Filter out the "--- Questions from" lines before joining for the last block
                filtered_block = [
                    line for line in current_question_block_lines 
                    if not line.startswith("--- Questions from")
                ]
                parsed_questions.append("\n".join(filtered_block).strip())

    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found.")
        return
    except Exception as e:
        print(f"Error reading '{input_file}': {e}")
        return

    if not parsed_questions:
        print("No questions found in the input file.")
        return

    print(f"Found {len(parsed_questions)} question blocks. Generating answers...")

    # Generate answers for each full question block
    for i, full_question_text in enumerate(parsed_questions):
        print(f"Processing question block {i+1}/{len(parsed_questions)}: {full_question_text[:70]}...") # Show first 70 chars
        
        # Pass the entire block as the question to the Gemini API function
        answer = await generate_answer_with_gemini(full_question_text, api_key) 
        
        output_data.append({
            "question": full_question_text, # The entire block (context + question)
            "answer": answer
        })
        print(f"Finished question block {i+1}.")

    # Write the questions and answers to the output JSON file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
        print(f"\nSuccessfully generated answers and saved them to '{output_file}'.")
    except Exception as e:
        print(f"Error writing to '{output_file}': {e}")

if __name__ == "__main__":
    asyncio.run(main())
