let
    pkgs = import <nixpkgs>{};

    overriddenCryptography = pkgs.python37Packages.cryptography.override {
        openssl= pkgs.openssl_1_1;
    };
    nativePythonPackages = with pkgs.python37Packages; [flask];
    customPythonPackages =  [ overriddenCryptography ];
    output = import ../buildPythonAppAndEnv.nix rec {
        inherit pkgs;
        pname = "libMLS";
        version = "0.1";

        src = ./.;

        propagatedBuildInputs = builtins.concatLists [ nativePythonPackages customPythonPackages ];
        checkInputs = with pkgs.python37Packages; [ pytest pylint pytestcov pytest-dependency];
    };
in output
