# special thanks to tfc for the inspiration https://github.com/tfc/nix_cmake_example/blob/master/release.nix

{
  nixpkgs ? null
}:

let
    pkgs = import ../pinned-nixpkgs.nix{inherit nixpkgs;};
in
    with pkgs;
let
    dirserver = import ./dirserver/default.nix  {inherit nixpkgs;};
    integration_test = import ./integration-tests.nix {inherit nixpkgs;};

# symlink join merges two derivations
in symlinkJoin {
    name ="mls-infrastructure";
    paths = [ dirserver ];
}