import requests

def run_prompt_on_ollama(model_name, prompt):
    # Replace 'YOUR_API_URL' with the actual URL of the Ollama API endpoint
    api_url = f"https://api.ollama.com/v1/models/{model_name}/generate"

    # Prepare the payload for the API request
    payload = {
        "prompt": prompt,
        # Add any other required parameters as per the Ollama API documentation
    }

    # Make a POST request to the Ollama API
    response = requests.post(api_url, json=payload)

    # Check if the request was successful
    if response.status_code == 200:
        result = response.json()
        print("Result from Ollama API:")
        print(result)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def main():
    model_name = input("Enter the model name: ")
    prompt = input("Enter the prompt: ")

    run_prompt_on_ollama(model_name, prompt)

if __name__ == "__main__":
    main()
