{
  nixpkgs ? null
}:

let
    pkgs = import ./pinned-nixpkgs.nix{inherit nixpkgs;};
in
   with pkgs;
let

    infrastructure = import ./infrastructure/default.nix {inherit nixpkgs;};
    libMLS = import ./libMLS/default.nix {inherit nixpkgs;};

    #integration_test = import ./integration-tests.nix;

    # symlink join merges two derivations
    output = pkgs.symlinkJoin {
        name ="mls";
        paths = [ infrastructure libMLS ];
    };

in output