vim.api.nvim_create_autocmd("FileType", {
	pattern = "man",
	callback = function()
		dofile(vim.fn.stdpath("config") .. "/lua/config/options.lua")
	end,
})
