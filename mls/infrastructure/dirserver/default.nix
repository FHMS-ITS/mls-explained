with import <nixpkgs> {};
with python37Packages;

#see https://nixos.org/nixpkgs/manual/#building-packages-and-applications
python37Packages.buildPythonApplication rec {
  pname = "mls-dirserver";
  version = "1.0";

  src = ./.;
  propagatedBuildInputs = with python37Packages; [ flask ];

  checkInputs =  with python37Packages; [ pytest pylint ];

  doCheck = true;

  checkPhase = ''
    py.test tests
  '';
}
