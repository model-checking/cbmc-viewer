#!/bin/bash

################################################################
# Documentation
#
# compgen, complete:
#   https://www.gnu.org/software/bash/manual/html_node/Programmable-Completion-Builtins.html
# _filedir:
#   https://github.com/nanoant/bash-completion-lib/blob/master/include/_filedir

################################################################
# Options
#
# omit deprecated options: --block --htmldir --srcexclude --blddir --storm

common_options="--help -h --verbose --debug --version"

viewer_options="--result --coverage --property --srcdir --exclude --extensions --source-method --wkdir --goto --reportdir --json-summary --viewer-coverage --viewer-loop --viewer-property --viewer-reachable --viewer-result --viewer-source --viewer-symbol --viewer-trace --config"
viewer_subcommands="coverage loop property reachable result source symbol trace"

coverage_options="--coverage --srcdir --viewer-coverage"
loop_options="--srcdir --goto --viewer-loop"
property_options="--property --srcdir --viewer-property"
reachable_options="--srcdir --goto --viewer-reachable"
result_options="--result --viewer-result"
source_options="--srcdir --exclude --extensions --source-method --wkdir --goto --viewer-source"
symbol_options="--srcdir --wkdir --goto --viewer-source --viewer-symbol"
trace_options="--result --srcdir --wkdir --viewer-trace"

_core_autocomplete()
{
    local options=$1
    local subcommands=$2
    local cur=${COMP_WORDS[COMP_CWORD]}
    local prev=${COMP_WORDS[COMP_CWORD-1]}

    case "$prev" in
        --srcdir|--wkdir)
            _filedir -d
            return 0
            ;;

        --result|--coverage|--property)
            # typically *.txt, *.xml, *.json
            _filedir
            return 0
            ;;

        --goto)
            # typically *.goto
            _filedir
            return 0
            ;;

        --json-summary)
            # typically *.json
            _filedir
            return 0
            ;;

        --config)
            # typically cbmc-viewer.json
            _filedir
            return 0
            ;;

        --viewer-coverage|--viewer-loop|--viewer-property|--viewer-reachable|--viewer-result|--viewer-source|--viewer-symbol|--viewer-trace)
            # typically viewer-*.json
            _filedir
            return 0
            ;;

        --reportdir)
            # typically report
            _filedir -d
            return 0
            ;;

        --source-method)
            # typically report
            COMPREPLY=( $( compgen -W "goto find walk make" -- $cur ) )
            _filedir -d
            return 0
            ;;

        coverage)
            COMPREPLY=( $( compgen -W "$coverage_options $common_options" -- $cur ) )
            return 0
            ;;
        loop)
            COMPREPLY=( $( compgen -W "$loop_options $common_options" -- $cur ) )
            return 0
            ;;
        property)
            COMPREPLY=( $( compgen -W "$property_options $common_options" -- $cur ) )
            return 0
            ;;
        reachable)
            COMPREPLY=( $( compgen -W "$reachable_options $common_options" -- $cur ) )
            return 0
            ;;
        result)
            COMPREPLY=( $( compgen -W "$result_options $common_options" -- $cur ) )
            return 0
            ;;
        source)
            COMPREPLY=( $( compgen -W "$source_options $common_options" -- $cur ) )
            return 0
            ;;
        symbol)
            COMPREPLY=( $( compgen -W "$symbol_options $common_options" -- $cur ) )
            return 0
            ;;
        trace)
            COMPREPLY=( $( compgen -W "$trace_options $common_options" -- $cur ) )
            return 0
            ;;


    esac

    if [[ "$cur" == -* ]]; then
        COMPREPLY=( $( compgen -W "$options $common_options" -- $cur ) )
        return 0
    fi

    COMPREPLY=( $( compgen -W "$options $common_options $subcommands" -- $cur ) )
    return 0
}

_viewer_autocomplete()
{
    _core_autocomplete "$viewer_options" "$viewer_subcommands"
}

complete -F _viewer_autocomplete cbmc-viewer
