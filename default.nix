with import <nixpkgs> {};

# special thanks to tfc for the inspiration https://github.com/tfc/nix_cmake_example/blob/master/release.nix

let
    infrastructure = import ./infrastructure/default.nix;
    libMLS = import ./libMLS/default.nix;

    #todo: Infrastructure
    #integration_test = import ./integration-tests.nix;

    # symlink join merges two derivations
in symlinkJoin {
    name ="mls";
    paths = [ infrastructure libMLS ];
}
