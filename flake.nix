{
  description = "pyser dev environment";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "aarch64-darwin";
      pkgs = import nixpkgs { inherit system; };
    in {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [
          (pkgs.python311.withPackages (ps: with ps; [
            # 必要なライブラリをここに
          ]))
        ];
      };
    };
}
