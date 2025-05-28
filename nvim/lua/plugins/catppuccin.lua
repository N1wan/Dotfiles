return { 
	"catppuccin/nvim", 
	name = "catppuccin", 
	priority = 1000, 
	opts = {
		flavour = "mocha", -- latte, frappe, macchiato, mocha
		transparent_background = false,
		show_end_of_buffer = true, -- shows the '~' characters after the end of buffers
		compile_path = vim.fn.stdpath("cache") .. "/catppuccin",
		compile = true,
		styles = { -- Handles the styles of general hi groups (see `:h highlight-args`):
			comments = { "italic" }, -- Change the style of comments
			conditionals = { "italic" },
			loops = {},
			functions = {},
			keywords = {},
			strings = {},
			variables = {},
			numbers = {},
			booleans = {},
			properties = {},
			types = {},
			operators = {},
			-- miscs = {}, -- Uncomment to turn off hard-coded styles
		},
		default_integrations = true,
		integrations = {
			treesitter = true,
			native_lsp = {
				enabled = true,
				virtual_text = {
					errors = { "italic" },
					hints = { "italic" },
					warnings = { "italic" },
					information = { "italic" },
				},
				underlines = {
					errors = { "underline" },
					hints = { "underline" },
					warnings = { "underline" },
					information = { "underline" },
				},
			},
			telescope = true,
			which_key = true,
			lsp_trouble = true,
			cmp = true,
			gitsigns = true,
			nvimtree = true,
			notify = true,
			mini = true,
		},
	},	
	config = function(_, opts)
		local catppuccin = require("catppuccin")
		catppuccin.setup(opts)
		vim.cmd.colorscheme("catppuccin")
	end,
}
