vim.g.mapleader = " "
vim.g.maplocalleader = " "

-- open oil file explorer
vim.keymap.set('n', '<leader>pf', ':Oil<Enter>', { noremap = true, silent = true })

-- clear search with escape
vim.keymap.set('n', '<esc>', ':noh<return><esc>', { noremap = true, silent = true })

-- open diagnostics
vim.api.nvim_set_keymap('n', '<leader>do', '<cmd>lua vim.diagnostic.open_float()<CR>', { noremap = true, silent = true })
vim.api.nvim_set_keymap('n', '<leader>dp', '<cmd>lua vim.diagnostic.goto_prev()<CR>', { noremap = true, silent = true })
vim.api.nvim_set_keymap('n', '<leader>dn', '<cmd>lua vim.diagnostic.goto_next()<CR>', { noremap = true, silent = true })

