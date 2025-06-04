return {
  "mason-org/mason-lspconfig.nvim",
  event = "BufReadPost",
  dependencies = {
    "mason-org/mason.nvim",
    "neovim/nvim-lspconfig",
  },
  opts = {
    ensure_installed = {
      "asm_lsp",
      "clangd",
      "cmake",
      "lua_ls",
      "vimls",
	  "jdtls",
    },
    automatic_installation = true,
  },
}
