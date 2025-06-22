#!/bin/bash

# Function to list available models
_list_models() {
    local cur prev words cword
    COMPREPLY=()
    _get_comp_words_by_ref -n : cur prev words cword
    MODELS=$(${COMP_WORDS[0]} list-models --plain)
    COMPREPLY=( $(compgen -W "${MODELS}" -- ${cur}) )
}

# Function to generate completions for the 'generate' command
_complete_generate() {
    local cur prev words cword
    _get_comp_words_by_ref -n : cur prev words cword

    case $cword in
        1)
            COMPREPLY=( $(compgen -W "generate chat list-models" -- ${cur}) )
            ;;
        2)
            if [[ $prev == "-m" || $prev == "--model_name" ]]; then
                _list_models
            else
                COMPREPLY=( $(compgen -W "" -- ${cur}) )
            fi
            ;;
        *)
            COMPREPLY=( $(compgen -W "" -- ${cur}) )
            ;;
    esac
}

# Function to generate completions for the 'chat' command
_complete_chat() {
    local cur prev words cword
    _get_comp_words_by_ref -n : cur prev words cword

    case $cword in
        1)
            COMPREPLY=( $(compgen -W "generate chat list-models" -- ${cur}) )
            ;;
        2)
            if [[ $prev == "-m" || $prev == "--model_name" ]]; then
                _list_models
            else
                COMPREPLY=( $(compgen -W "" -- ${cur}) )
            fi
            ;;
        *)
            COMPREPLY=( $(compgen -W "" -- ${cur}) )
            ;;
    esac
}

# Function to generate completions for the 'list-models' command
_complete_list_models() {
    local cur prev words cword
    _get_comp_words_by_ref -n : cur prev words cword

    case $cword in
        1)
            COMPREPLY=( $(compgen -W "generate chat list-models" -- ${cur}) )
            ;;
        *)
            COMPREPLY=( $(compgen -W "" -- ${cur}) )
            ;;
    esac
}

# Main completion function
_complete_ocelot_cli() {
    local cur prev words cword
    _get_comp_words_by_ref -n : cur prev words cword

    case $cword in
        1)
            COMPREPLY=( $(compgen -W "generate chat list-models" -- ${cur}) )
            ;;
        2)
            if [[ $prev == "-m" || $prev == "--model_name" ]]; then
                _list_models
            else
                COMPREPLY=( $(compgen -W "" -- ${cur}) )
            fi
            ;;
        *)
            COMPREPLY=( $(compgen -W "" -- ${cur}) )
            ;;
    esac
}

complete -F _complete_ocelot_cli ocelot_cli
