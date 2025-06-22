_ocelot_cli_list_models_cached() {
    local cli="$1"
    local CACHE_FILE="$HOME/.cache/ocelot_cli_model_list.txt"
    local CACHE_DURATION=3600  # 1 hour
    if [[ ! -f "$CACHE_FILE" || $(( $(date +%s) - $(stat -c %Y "$CACHE_FILE") )) -gt $CACHE_DURATION ]]; then
      mkdir -p "$(dirname "$CACHE_FILE")"
      "$cli" list-models --plain > "$CACHE_FILE" 2>/dev/null || true
    fi
    cat "$CACHE_FILE"
}

_ocelot_cli_completions() {
    COMP_WORDBREAKS=${COMP_WORDBREAKS//:/}
    local cur prev words cword
    _get_comp_words_by_ref -n : cur prev words cword

    local script="${COMP_WORDS[0]}"
    local commands="generate chat list-models"

    if [[ $cword -eq 1 ]]; then
        COMPREPLY=( $(compgen -W "$commands" -- "$cur") )
        return 0
    fi

    # Detect subcommand (primeiro token não-flag)
    local cmd=""
    for (( i=1; i < ${#COMP_WORDS[@]}; i++ )); do
        local word="${COMP_WORDS[i]}"
        if [[ "$word" != -* ]]; then
            cmd="$word"
            break
        fi
    done

    # Se ainda estamos completando o subcomando (cword == 1)
    if [[ -z "$cmd" && $cword -eq 1 ]]; then
        COMPREPLY=( $(compgen -W "$commands" -- "$cur") )
        return 0
    fi

    # Se cmd está parcialmente digitado (ex: 'ge'), complete como subcomando
    if [[ -z "$cmd" ]]; then
        COMPREPLY=( $(compgen -W "$commands" -- "$cur") )
        return 0
    fi

    case "$cmd" in
        generate|chat)
            if [[ "$prev" == "-m" || "$prev" == "--model_name" ]]; then
                local models=$(_ocelot_cli_list_models_cached "$script")
                COMPREPLY=( $(compgen -W "$models" -- "$cur") )
                return 0
            fi
            COMPREPLY=( $(compgen -W "-m --model_name --no-show-reasoning --plain --debug" -- "$cur") )
            ;;
        list-models)
            COMPREPLY=( $(compgen -W "-p --provider_name --plain --debug" -- "$cur") )
            ;;
    esac
}

complete -F _ocelot_cli_completions ocelot_cli
