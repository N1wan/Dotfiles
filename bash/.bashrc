#
# ~/.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return


# aliases

alias ls='ls --color=auto'
alias ll='ls --color=auto -la'

alias grep='grep --color=auto'

alias lg='lazygit'



PS1='[\u@\h \W]\$ '
