return {
	"nvim-treesitter/nvim-treesitter",
	lazy = false,
	branch = 'main',
	build = ":TSUpdate",
	event = "BufReadPost",
	cmd = {
		"TSInstall",
		"TSUpdate",
		"TSInstallInfo",
		"TSEnable",
		"TSDisable",
		"TSModuleInfo",
		"TSUninstall",
	},
	opts = {
		ensure_installed = {
			"asm",
			"lua",
			"vim",
			"c",
			"markdown",
			"markdown_inline",
			"gitignore",
		},
		highlight = {
			enable = true,
			additional_vim_regex_highlighting = false,
		},
		indent = {
			enable = true,
		},
	},
}
