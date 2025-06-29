
fastfetch

# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

# To customize prompt, run `p10k configure` or edit ~/.p10k.zsh.
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh

typeset -g POWERLEVEL9K_INSTANT_PROMPT=quiet

# Set the directory to store zinit and plugins
ZINIT_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/zinit/zinit.git"

# Download Zinit, if it's not there yet
if [ ! -d "$ZINIT_HOME" ]; then
	mkdir -p "$(dirname $ZINIT_HOME)"
	git clone https://github.com/zdharma-continuum/zinit.git "$ZINIT_HOME"
fi

# Source/Load zinit
source "${ZINIT_HOME}/zinit.zsh"

# Add in Powerlevel10k
zinit ice depth=1; zinit light romkatv/powerlevel10k

# Add in zsh plugins
zinit light zsh-users/zsh-syntax-highlighting
zinit light zsh-users/zsh-completions
zinit light zsh-users/zsh-autosuggestions
zinit light Aloxaf/fzf-tab

# Add in snippets
zinit snippet OMZP::sudo

# Load completions
autoload -U compinit && compinit

zinit cdreplay -q

# Keybindings
# bindkey -v
# bindkey '^p' history-search-backward
# bindkey '^n' history-search-forward
# bindkey "^[[3~" delete-char

bindkey -v
bindkey -M vicmd 'k' history-search-backward
bindkey -M vicmd 'j' history-search-forward
bindkey "^[[3~" delete-char

# History
HISTSIZE=5000
HISTFILE=~/.zsh_history
SAVEHIST=$HISTSIZE
HISTDUP=erase
setopt appendhistory
setopt sharehistory
setopt hist_ignore_space
setopt hist_ignore_all_dups
setopt hist_save_no_dups
setopt hist_ignore_dups
setopt hist_find_no_dups

# Completion styling
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Za-z}'
zstyle ':completion:*' list-colors '${(s.:.)LS_COLORS}'
zstyle ':completion:*' menu no

# environment variables
export MANPAGER='nvim +Man!'

# Aliases
alias ls='ls --color'
alias ll='ls -la'
alias clear='clear; fastfetch'
alias c='clear'
alias grep='grep --color'
alias timg='timg -pk'
alias tls='tmux ls'
alias lg='lazygit'
systemctl() {
	case "$1" in
		hibernate|suspend|suspend-then-hibernate|hybrid-sleep|hybrid-hibernate)
			dm-tool lock
			command systemctl "$@"
			;;
		*)
			command systemctl "$@"
			;;
	esac
}

# Shell integrations
eval "$(fzf --zsh)"
eval "$(zoxide init --cmd cd zsh)"

