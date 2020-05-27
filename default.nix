{
  nixpkgs ? null
}:

let
    pkgs = import ./pinned-nixpkgs.nix{inherit nixpkgs;};
in
   with pkgs;
let

    libMLS = import ./libMLS/default.nix {inherit nixpkgs;};
    infrastructure = import ./infrastructure/default.nix {inherit nixpkgs libMLS;};

in pkgs.linkFarm "mls" [ {name="infrastructure"; path=infrastructure;} {name="libMLS";path=libMLS;} ]
