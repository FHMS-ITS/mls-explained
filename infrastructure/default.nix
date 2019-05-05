with import <nixpkgs>{};

{
	dirserver = import ./dirserver/default.nix;
	integration_test_results = import ./integration-tests.nix;
}

