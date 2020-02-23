{
    nixpkgs ? null
}:

let
  spec =
  {
    owner = "NixOS";
    repo = "nixpkgs";
    rev = "1fe82110febdf005d97b2927610ee854a38a8f26";
    sha256 = "08x6saa7iljyq2m0j6p9phy0v17r3p8l7vklv7y7gvhdc7a85ppi";

  };
  url = "https://github.com/${spec.owner}/${spec.repo}/archive/${spec.rev}.tar.gz";

  nixpkgsSrc =
    if isNull nixpkgs
      then
        builtins.fetchTarball {url = url; sha256 = spec.sha256;}
      else nixpkgs;

  pkgs = import nixpkgsSrc{};

in pkgs
