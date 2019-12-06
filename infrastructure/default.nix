{
    nixpkgs ? null,
    libMLS ? import ../libMLS/default.nix {}
}:

let
    pkgs = import ../pinned-nixpkgs.nix{inherit nixpkgs;};
in
   with pkgs;
let

    output = python37Packages.buildPythonApplication rec {
        pname = "infrastructure";
        version = "0.1";

        src = ./.;

        propagatedBuildInputs = [ python37Packages.flask python37Packages.requests libMLS];
        checkInputs = with python37Packages; [ pytest pylint pytestcov ];

        checkPhase = ''
            mkdir -p $out/logs
            PYLINTRC=$src/.pylintrc py.test -s --cov=$pname tests | tee $out/logs/test.log
          '';

    };
in output
