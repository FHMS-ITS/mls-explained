#with import <nixpkgs>{};

#{
#	dirserver = import ./dirserver/default.nix;
#	integration_test_results = import ./integration-tests.nix;
#}

with (import <nixpkgs> {});

let
    dirserver = import ./dirserver/default.nix;
    integration_test = import ./integration-tests.nix;

in derivation {

    name = "mls-infrastructure";
    inherit coreutils dirserver integration_test;
    builder = "${bash}/bin/bash";
    args = [ ./infrastructure_builder.sh ];
    system = builtins.currentSystem;
    src = ./.;
}
