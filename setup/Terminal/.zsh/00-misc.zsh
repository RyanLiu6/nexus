# PyEnv, need other in ~/.zprofile (found at PyEnv documentation)
eval "$(pyenv init -)"

# iTerm 2 tab name for directories
if [ $ITERM_SESSION_ID ]; then
    precmd() {
    echo -ne "\e]0;${PWD##*/}\a"
    }
fi

# Homebrew completions
if type brew &>/dev/null; then
    FPATH="$(brew --prefix)/share/zsh/site-functions:${FPATH}"

    autoload -Uz compinit
    compinit
fi

# Then zsh completions
if type brew &>/dev/null; then
    FPATH=$(brew --prefix)/share/zsh-completions:$FPATH

    autoload -Uz compinit
    compinit
fi
