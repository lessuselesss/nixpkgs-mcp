{
  description = "Nixpkgs MCP Server - Dynamic tool generation for all nixpkgs packages";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # Python package for the MCP server
        nixpkgs-mcp-server = pkgs.python3Packages.buildPythonApplication {
          pname = "nixpkgs-mcp-server";
          version = "0.1.0";

          src = pkgs.lib.cleanSourceWith {
            src = ./.;
            filter = path: type:
              let
                baseName = baseNameOf path;
              in
              # Exclude result symlink and common build artifacts
              baseName != "result" &&
              !pkgs.lib.hasPrefix ".claude" baseName;
          };

          pyproject = true;

          build-system = [
            pkgs.python3Packages.hatchling
          ];

          dependencies = with pkgs.python3Packages; [
            mcp
          ];

          meta = {
            description = "MCP server that dynamically exposes nixpkgs packages as tools";
            license = pkgs.lib.licenses.unlicense;
          };
        };

      in
      {
        packages = {
          default = nixpkgs-mcp-server;
          nixpkgs-mcp-server = nixpkgs-mcp-server;
        };

        apps = {
          default = {
            type = "app";
            program = "${nixpkgs-mcp-server}/bin/nixpkgs-mcp-server";
          };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python3
            python3Packages.mcp
            python3Packages.hatchling
            nix  # For executing packages
          ];

          shellHook = ''
            echo "🚀 Nixpkgs MCP Server Development Environment"
            echo "Run: python server.py to start the server"
            echo "Or: nix run . to run the packaged version"
          '';
        };

        # Helper to generate .mcp.json configuration
        packages.mcp-config = pkgs.writeTextFile {
          name = "mcp-config.json";
          text = builtins.toJSON {
            mcpServers = {
              nixpkgs = {
                command = "nix";
                args = [ "run" "path:${self}" ];
                env = {};
              };
            };
          };
        };
      }
    );
}
