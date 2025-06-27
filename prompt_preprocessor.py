import re
from pathlib import Path

class PromptPreprocessor:
    def __init__(self):
        self.file_reference_pattern = re.compile(r'@@(\w+)')

    def process_prompt(self, prompt: str) -> str:
        def replace_file_reference(match):
            file_name = match.group(1)
            file_path = Path(file_name)
            if file_path.exists() and file_path.is_file():
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                return f"{file_name}\n===\n{content}\n===\n"
            else:
                return match.group(0)  # Return the original reference if file not found

        return self.file_reference_pattern.sub(replace_file_reference, prompt)

# Example usage
if __name__ == "__main__":
    preprocessor = PromptPreprocessor()
    prompt = "This is a test prompt with multiple file references @@example1.txt and @@example2.txt."
    processed_prompt = preprocessor.process_prompt(prompt)
    print(processed_prompt)
