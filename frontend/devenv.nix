{ pkgs, lib, config, inputs, ... }:

{
  # https://devenv.sh/basics/
  env.GREET = "devenv";

  # https://devenv.sh/packages/
  packages = [
    pkgs.git
    pkgs.nodejs_20
    pkgs.nodePackages.pnpm
  ];

  # https://devenv.sh/scripts/
  scripts.hello.exec = ''
    echo hello from $GREET
  '';

  enterShell = ''
    echo "🚀 Next.js Frontend Development Environment"
    echo "Node.js version: $(node --version)"
    echo "pnpm version: $(pnpm --version)"
    echo ""
    echo "Run 'pnpm install' to install dependencies"
    echo "Run 'pnpm dev' to start the development server"
  '';

  # https://devenv.sh/languages/
  languages.javascript.enable = true;
  languages.javascript.npm.enable = true;

  # https://devenv.sh/pre-commit-hooks/
  # pre-commit-hooks.hooks.shellcheck.enable = true;

  # See full reference at https://devenv.sh/reference/options/
}

