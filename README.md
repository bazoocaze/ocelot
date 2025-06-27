# Ocelot CLI - Jaguatirica Command Line Interface for LLM Models

## Overview
`ocelot_cli` is a command-line interface (CLI) tool designed to interact with large language models (LLMs) through various backends. It supports generating text from prompts, engaging in interactive chats, and listing available models. The tool is built with Python and uses the `rich` library for enhanced terminal output.

## Features
- **Generate Text**: Run prompts against specified LLM models.
- **Interactive Chat**: Engage in real-time conversations with models.
- **Model Management**: List available models from supported backends.
- **Rich Output**: Styled terminal output using the `rich` library.
- **Extensible Architecture**: Supports multiple providers like Ollama, OpenRouter, and more.
- **Prompt Preprocessor**: Automatically include file contents in prompts using file references.

## Prerequisites
- Python 3.12
- `pipenv` (for dependency management)

## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/ocelot_cli.git
   cd ocelot_cli
   ```

2. **Install Dependencies**
   ```bash
   pipenv install
   ```

3. **Run the CLI**
   ```bash
   ./ocelot_cli.sh
   ```

> **Note**: The script `ocelot_cli.sh` automatically sets up a virtual environment using `pipenv` and runs the Python script.

## Usage

### Basic Commands

#### 1. **Generate Text**
```bash
./ocelot_cli.sh generate -m <model_name> [prompt]
```
- **Example**:
  ```bash
  ./ocelot_cli.sh generate -m ollama/llama2 "Explain quantum computing in simple terms."
  ```
- **If prompt is not provided, the command will read from standard input.**
- **Example using pipe**:
  ```bash
  echo "Explain quantum computing in simple terms." | ./ocelot_cli.sh generate -m ollama/llama2
  ```

#### 2. **Interactive Chat**
```bash
./ocelot_cli.sh chat -m <model_name> [ --initial-prompt "<prompt>" ]
```
- **Example**:
  ```bash
  ./ocelot_cli.sh chat -m openrouter/gpt-3.5 --initial-prompt "Hi, how are you?"
  ```
- **Exit Chat**: Type `exit` to quit.

#### 3. **List Available Models**
```bash
./ocelot_cli.sh list-models [ -p <provider_name> ]
```
- **Example**:
  ```bash
  ./ocelot_cli.sh list-models -p ollama
  ```

## Options

| Option | Description |
|--------|-------------|
| `--debug` | Enable debug mode for detailed logs. |
| `--plain` | Disable rich formatting for output. |
| `--no-show-reasoning` | Hide the model's reasoning process during generation. |
| `--initial-prompt` | Provide a starting prompt for interactive chat. |

## Example Workflows

### Generate Text
```bash
./ocelot_cli.sh generate -m openrouter/gpt-3.5 "Write a short story about a robot."
```

### Generate Text using Pipe
```bash
echo "Write a short story about a robot." | ./ocelot_cli.sh generate -m openrouter/gpt-3.5
```

### Interactive Chat
```bash
./ocelot_cli.sh chat -m ollama/llama2 --initial-prompt "What is the capital of France?"
```

### List Models
```bash
./ocelot_cli.sh list-models -p all
```

## Dependencies

- `requests` (for API interactions)
- `rich` (for styled terminal output)
- `pyyaml` (for config loading)

## Configuration

The tool uses a `ConfigLoader` to manage backend configurations. Ensure your `.env` file (if used) is correctly set up in the project root.

## Prompt Preprocessor

The `prompt_preprocessor` feature allows you to include the contents of files in your prompts. To use this feature, include a file reference in your prompt using the `@@filename` syntax. The preprocessor will automatically replace the reference with the file's contents.

### Example

Given a file named `example.txt` with the following content:
```
This is an example file.
```

You can include its contents in a prompt like this:
```
Explain the following text: @@example.txt
```

The preprocessor will replace `@@example.txt` with the actual contents of the file:
````
Explain the following text:

FILE: example.txt
```
This is an example file.
```
````

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Commit your changes.
4. Push to the branch and submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
