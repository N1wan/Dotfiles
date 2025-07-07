
-- Make relative line numbers default
vim.o.number = true
vim.o.relativenumber = true

-- make the tab size 4
vim.o.shiftwidth = 4
vim.o.tabstop = 4
vim.o.expandtab = true -- use spaces for tabs

-- Sync clipboard between OS and Neovim.
-- Schedule the setting after `UiEnter` because it can increase startup-time.
vim.schedule(function()
  vim.o.clipboard = 'unnamedplus'
end)

-- Save undo history
vim.o.undofile = true
vim.o.undodir = vim.fn.stdpath("data") .. "/undo"

-- Case-insensitive searching UNLESS \C or one or more capital letters in the search term
vim.o.ignorecase = true
vim.o.smartcase = true

-- Set scrolloff so cursor stays closer to the center
vim.o.scrolloff = 12

-- Dont show what mode im in
vim.o.showmode = false
