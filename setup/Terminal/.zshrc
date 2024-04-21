# source: https://github.com/xero/dotfiles
for config in ~/dev/focus/setup/Terminal/.zsh/*.zsh; do source $config; done
for config in ~/dev/focus/setup/ignore/*.zsh; do source $config; done

# Set Spaceship ZSH as a prompt
autoload -U promptinit; promptinit
prompt spaceship

# Spaceship options
SPACESHIP_PROMPT_ORDER=(
  user          # Username section
  host          # Hostname section
  dir           # Current directory section
  git           # Git section (git_branch + git_status)
  node          # Node.js section
  docker        # Docker section
  pyenv         # Pyenv section
)

# General stuff
export SPACESHIP_USER_SHOW="always"
export SPACESHIP_HOST_SHOW="always"
export SPACESHIP_DIR_TRUNC=0

# Colors
export LSCOLORS="Gx"
export SPACESHIP_DIR_COLOR="cyan"
export SPACESHIP_HOST_COLOR="yellow"
export SPACESHIP_USER_COLOR="magenta"
export SPACESHIP_GIT_BRANCH_COLOR="green"
