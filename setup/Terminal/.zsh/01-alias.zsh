#  Overriding defaults
alias ls="ls -hFG"
alias grep="grep -i"
alias mkdir="mkdir -p"
alias systemctl="sudo systemctl"

# Custom aliases
alias reload="source ~/.zshrc && echo 'Profiles reloaded correctly' || echo 'Syntax Errors'"
alias cdm="cd ~/dev/focus/"

# functions
function pip_install {
    pip install $1 && pip freeze | grep $1 >> requirements.txt
}
