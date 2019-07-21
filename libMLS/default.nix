let
    pkgs = import <nixpkgs>{};
    output = import ../infrastructure/buildPythonAppAndEnv.nix rec {
        inherit pkgs;
        pname = "libMLS";
        version = "0.1";

        src = ./.;

        propagatedBuildInputs = with pkgs.python37Packages; [ flask cryptography ];
        checkInputs = with pkgs.python37Packages; [ pytest pylint pytestcov ];
    };
in output
