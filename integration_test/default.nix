{
  nixpkgs ? null
}:

let
   pkgs = import ../pinned-nixpkgs.nix{inherit nixpkgs;};
in
   with pkgs;
let

   project = import ../default.nix {inherit nixpkgs;};

in writeScript "mls-integration-test" ''
#!${bash}/bin/bash

function cleanup {
     echo "cleaning up"
     #unset -e
     #unset -u
     rm ./alice
     rm ./bob

     rm ./init_key_store.json || true
     rm ./message_store.json || true

     kill $DIRSERVER_PID
     kill $ALICE_PID || true
     kill $BOB_PID || true
}
trap cleanup EXIT


MKTEMP=${mktemp}/bin/mktemp
DIRSERVER=${project}/infrastructure/bin/mls-dir-server
CHATCLIENT=${project}/infrastructure/bin/mls-chat-client
MKFIFO=${coreutils}/bin/mkfifo



set -e
set -u
$MKFIFO alice
$MKFIFO bob

$DIRSERVER &
DIRSERVER_PID=$!

$CHATCLIENT --user "alice" <alice &
ALICE_PID=$!
$CHATCLIENT --user "bob" <bob &>/dev/null &
BOB_PID=$!

echo 4 > bob     #New Init Key
echo 1234 > bob

echo 4 > alice     #New Init Key
echo 4321 > alice

#sleep 3

echo 5 > alice
echo "mygroup" > alice

echo 6 >alice
echo -e "mygroup\nbob">alice
#sleep 1
#echo "bob">alice

sleep 1

echo 2 > bob


echo 99 > bob
echo 99 > alice

wait $BOB_PID


''


