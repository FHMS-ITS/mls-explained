with (import <nixpkgs> {});

rustPlatform.buildRustPackage rec {
  name = "mls-rust";

  buildInputs = [ python36 ];
  
  system = builtins.currentSystem;
  src = ./.;

  cargoSha256 = "0ad3kk48fx15rs16c4mnh0dkaj25qjwbkjacv8jfnka0iq29ys5j";
}

