# Ocelot CLI

Ocelot CLI is a command-line interface for interacting with large language models. It supports multiple providers and allows for both text generation and interactive chat sessions.

## Features

- Generate text from prompts using various language models.
- Interactive chat with language models.
- List available models from configured providers.
- Supports multiple backend providers (Ollama, OpenRouter, etc.).
- Configurable via a YAML configuration file.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/bazoocaze/ocelot.git
   cd ocelot
   ```

2. Install dependencies using pipenv:
   ```bash
   pipenv install
   ```

3. Set up your configuration file (optional):
   Create a `config.yml` file in the `.config/ocelot-cli/` directory with your provider configurations.

## Usage

### Generate Text

To generate text from a prompt, use the following command:
