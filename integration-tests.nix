with import <nixpkgs>{};

#losely based on https://stackoverflow.com/questions/43837691/how-to-package-a-single-python-script-with-nix
stdenv.mkDerivation {
  name = "integration-tests";
  buildInputs = [
    (python37.withPackages (pythonPackages: with pythonPackages; [
      pytest
      pylint
      flask
    ]))
  ];
  src = ./.;
  unpackPhase = "true";
  installPhase = "true";
  doCheck = true;
  checkPhase = ''
    mkdir -p $out/logs
    mkdir -p ./temp
    cp -r $src/* ./temp
    cp $src/.pylintrc ./temp
    cd ./temp
    PYLINTRC=$src/.pylintrc python3 -m pytest -p no:cacheprovider tests | tee $out/logs/integration_test.log
  '';

}

