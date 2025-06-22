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
    local arguments="-h --help --plain -d --debug"

    if [[ $cword -eq 1 ]]; then
        COMPREPLY=( $(compgen -W "$commands" -- "$cur") )
        return 0
    fi

    case ${words[1]} in
        generate|chat)
            if [[ "$prev" == "-m" || "$prev" == "--model_name" ]]; then
                arguments="$(_ocelot_cli_list_models_cached "$script")"
            else
                arguments="${arguments} -m --model_name --no-show-reasoning --initial-prompt"
            fi
            ;;
        list-models)
            arguments="${arguments} --provider_name -p"
            ;;
    esac

    COMPREPLY=( $(compgen -W "${arguments}" -- "$cur") )
}

complete -F _ocelot_cli_completions ocelot_cli
