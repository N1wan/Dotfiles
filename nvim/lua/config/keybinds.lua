vim.g.mapleader = " "
vim.g.maplocalleader = " "

-- open oil file explorer
vim.keymap.set('n', '<leader>pf', ':Oil<Enter>', {})

-- clear search with escape
vim.keymap.set('n', '<esc>', ':noh<return><esc>', {})

