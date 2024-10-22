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

        propagatedBuildInputs = with python37Packages; [ flask requests libMLS pytestrunner qt5.full pyqt5 ];
        checkInputs = with python37Packages; [ pytest pylint pytest-pylint ];

        preCheck = ''
        export PYLINTRC=$src/.pylintrc;
        export PYLINTHOME=$out
        '';

    };

in pkgs.symlinkJoin {
  name = "mls-infrastructure-wrapped";
  paths = [ output ];
  buildInputs = [ makeWrapper ];
  postBuild = ''
    wrapProgram $out/bin/mls-chat-client-gui \
      --prefix PATH : ${graphviz}/bin
    wrapProgram $out/bin/mls-chat-client-tui \
      --prefix PATH : ${graphviz}/bin
  '';
}
