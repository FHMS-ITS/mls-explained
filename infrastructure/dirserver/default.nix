let
    pkgs = import <nixpkgs>{};
    output = import ../../buildPythonAppAndEnv.nix rec {
        inherit pkgs;
        pname = "dirserver";
        version = "0.1";

        src = ./.;

        propagatedBuildInputs = with pkgs.python37Packages; [ flask ];
        checkInputs = with pkgs.python37Packages; [ pytest pylint pytestcov ];
    };
in output