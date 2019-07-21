with import <nixpkgs> {};

# special thanks to tfc for the inspiration https://github.com/tfc/nix_cmake_example/blob/master/release.nix

let
    dirserver = import ./dirserver/default.nix;
    integration_test = import ./integration-tests.nix;

    # symlink join merges two derivations
in symlinkJoin {
    name ="mls-infrastructure";
    paths = [ dirserver ];
}
