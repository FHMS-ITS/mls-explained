{
    pkgs,
    python ? pkgs.python37,
    pythonPackages ? pkgs.python37Packages,
    pname,
    version,
    src,
    propagatedBuildInputs,
    checkInputs
}:

let
    #see https://nixos.org/nixpkgs/manual/#building-packages-and-applications
    app = pythonPackages.buildPythonApplication rec {
      inherit pname version src propagatedBuildInputs checkInputs;

      checkPhase = ''
        mkdir -p $out/logs
        PYLINTRC=$src/.pylintrc py.test -s --cov=$pname --include=$pname/$pname/* tests | tee $out/logs/test.log
      '';
    };

    # see https://nixos.org/nixpkgs/manual/#python.buildEnv-function
    env = python.buildEnv.override {
      extraLibs = builtins.concatLists [propagatedBuildInputs checkInputs] ;
      ignoreCollisions = true;
    };

    # a linkfarm creates a new derivation containing of subderivations which are placed in a subfolder called "name"
    output = pkgs.linkFarm pname [ { name = "app"; path = app; } { name ="env"; path=env; } ];

in output

