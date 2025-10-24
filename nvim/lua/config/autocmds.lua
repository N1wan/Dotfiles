vim.api.nvim_create_autocmd("FileType", {
	pattern = "man",
	callback = function()
		dofile(vim.fn.stdpath("config") .. "/lua/config/options.lua")
	end,
})

vim.api.nvim_create_autocmd("FileType", {
  pattern = { "javascript", "javascriptreact", "typescript", "typescriptreact" },
  callback = function()
    vim.bo.tabstop = 2
    vim.bo.shiftwidth = 2
    vim.bo.expandtab = true
  end,
})

