return {
  "mason-org/mason-lspconfig.nvim",
  event = "BufReadPost",
  lazy = false,
  dependencies = {
    "mason-org/mason.nvim",
    "neovim/nvim-lspconfig",
  },
  opts = {
    ensure_installed = {
      "asm_lsp",
      "clangd",
      "cmake",
      "gopls",
      "lua_ls",
      "vimls",
	  "jdtls",
    },
    automatic_installation = true,
  },
}
