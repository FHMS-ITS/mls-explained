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
    nativePythonPackages = with pkgs.python37Packages; [flask];
    customPythonPackages =  [ overriddenCryptography ];
    output = pkgs.python37Packages.buildPythonApplication rec {

        pname = "libMLS";
        version = "0.1";

        src = ./.;

        propagatedBuildInputs = builtins.concatLists [ nativePythonPackages customPythonPackages ];
        checkInputs = with pkgs.python37Packages; [ pytest pylint pytestcov pytest-dependency];

      checkPhase = ''
        mkdir -p $out/logs
        PYLINTRC=$src/.pylintrc py.test -s --cov=$pname tests | tee $out/logs/test.log
      '';
    };
in output
