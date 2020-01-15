{
  nixpkgs ? null
}:

let
    pkgs = import ../pinned-nixpkgs.nix{inherit nixpkgs;};
in

let

    overriddenCryptography = pkgs.python37Packages.cryptography.override {
        openssl= pkgs.openssl_1_1;
    };
    nativePythonPackages = with pkgs.python37Packages; [flask pytestrunner];
    customPythonPackages =  [ overriddenCryptography ];
    output = pkgs.python37Packages.buildPythonApplication rec {

        pname = "libMLS";
        version = "0.1";

        src = ./.;

        propagatedBuildInputs = builtins.concatLists [ nativePythonPackages customPythonPackages ];
        checkInputs = with pkgs.python37Packages; [ pytest pylint pytestcov pytest-dependency pytest-pylint];

        preCheck = ''
        export PYLINTRC=$src/.pylintrc;
        export PYLINTHOME=$out
        '';

      #doCheck = false;
    };
in output
