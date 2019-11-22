{
    nixpkgs ? null
}:

let
  spec =
  {
    owner = "NixOS";
    repo = "nixpkgs";
    rev = "58fb23f72ad916c8bbfa3c3bc2d0c83c9cfcdd16";
    sha256 =  "0f7gnsis5hdrdcmiv7s06qz02pszmmfxrqvc77jf0lmc86i25x9i";
  };
  url = "https://github.com/${spec.owner}/${spec.repo}/archive/${spec.rev}.tar.gz";

  nixpkgsSrc =
    if isNull nixpkgs
      then
        builtins.fetchTarball {url = url; sha256 = spec.sha256;}
      else nixpkgs;

  pkgs = import nixpkgsSrc{};

in pkgs
