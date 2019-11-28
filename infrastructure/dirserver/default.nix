{
  nixpkgs ? null
}:

let
    pkgs = import ../../pinned-nixpkgs.nix{inherit nixpkgs;};
in

let

    libmls = import ../../libMLS/default.nix{inherit nixpkgs;};
    output = pkgs.python37Packages.buildPythonApplication rec {
        pname = "dirserver";
        version = "0.1";

        src = ./.;

        propagatedBuildInputs = with pkgs.python37Packages; [ flask libmls ];
        checkInputs = with pkgs.python37Packages; [ pytest pylint pytestcov ];
    };
in output