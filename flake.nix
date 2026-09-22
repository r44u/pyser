{
  description = "pyser dev environment (Nix + pip hybrid)";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "aarch64-darwin";
      pkgs = import nixpkgs { inherit system; };
    in {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [
          (pkgs.python312.withPackages (ps: with ps; [
            pysdl2
            pyopengl
            numpy
          ]))
          pkgs.SDL2
          pkgs.SDL2_ttf
          pkgs.SDL2_image
        ];

        shellHook = ''
          # Nix管理のSDL2本体をpysdl2に明示的に教える(pysdl2-dllへのフォールバックを防ぐ)
          export PYSDL2_DLL_PATH="${pkgs.SDL2}/lib"

          if [ ! -d .venv ]; then
            python -m venv .venv --system-site-packages
            source .venv/bin/activate
            pip install dukpy skia-python
          else
            source .venv/bin/activate
          fi
        '';
      };
    };
}
