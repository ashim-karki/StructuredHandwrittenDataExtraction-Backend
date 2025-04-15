import google.generativeai as genai
import os
import json
import re
import dotenv

dotenv.load_dotenv()

def extract_key_value_with_llm(text_input: str, prompt_template: str = None):
    """
    Extracts key-value pairs from a whole text input using a Gemini LLM.

    Args:
        text_input: The input text from which to extract key-value pairs.
        prompt_template: A template for the prompt sent to the LLM.
                         It should contain "{text}" which will be replaced
                         with the input text. The template should guide the
                         LLM to output the key-value pairs in JSON format.
                         If None, a default template will be used.

    Returns:
        A dictionary representing the extracted key-value pairs, or None if
        the LLM response cannot be parsed into a dictionary.
    """
    # Set default prompt template if none provided
    if prompt_template is None:
        prompt_template = """
        Extract key-value pairs from the following text and return ONLY a valid JSON object.
        Do not include any explanations, markdown formatting, or code blocks in your response.
        Just return a clean JSON object where keys are the entity names and values are their corresponding values.

        Text:
        {text}
        """

    # Configure the Gemini API
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Please set the GOOGLE_API_KEY environment variable.")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')

    # Create the prompt
    prompt = prompt_template.format(text=text_input)

    try:
        # Generate the response
        response = model.generate_content(prompt)
        response_text = response.text
        
        # Clean up the response to extract just the JSON part
        # Remove markdown code blocks if present
        json_text = re.sub(r'^```json\s*|\s*```$', '', response_text, flags=re.MULTILINE)
        
        # Try to find JSON object between curly braces if still not clean
        match = re.search(r'\{.*\}', json_text, re.DOTALL)
        if match:
            json_text = match.group(0)
            
        # Remove any triple backticks without language specification
        json_text = re.sub(r'^```\s*|\s*```$', '', json_text, flags=re.MULTILINE)
        
        try:
            # Parse the cleaned JSON
            key_value_dict = json.loads(json_text)
            return key_value_dict
        except json.JSONDecodeError as e:
            print(f"Warning: LLM response was not valid JSON: {response_text}")
            print(f"JSON parse error: {e}")
            return None

    except Exception as e:
        print(f"An error occurred during LLM processing: {e}")
        return None