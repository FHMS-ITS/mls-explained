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

function cleanup_files {
     rm ./alice || true
     rm ./bob || true

     rm ./init_key_store.json || true
     rm ./message_store.json || true
}

function cleanup {

     echo -e "\n\n################## DIR SERVER OUTPUT ##################\n\n"
     cat $OUT_DIRSERVER
     echo -e "\n\n################## ALICE OUTPUT ##################\n\n"
     cat $OUT_ALICE
     echo -e "\n\n################## BOB OUTPUT ##################\n\n"
     cat $OUT_BOB

     cleanup_files

     kill $DIRSERVER_PID
     kill $ALICE_PID &>/dev/null || true
     kill $BOB_PID &>/dev/null || true
}
trap cleanup EXIT

cleanup_files

MKTEMP=${mktemp}/bin/mktemp
DIRSERVER=${project}/infrastructure/bin/mls-dir-server
CHATCLIENT=${project}/infrastructure/bin/mls-chat-client-tui
MKFIFO=${coreutils}/bin/mkfifo
GREP=${pcre}/bin/pcregrep
#GREP=${coreutils}/bin/grep
WC=${coreutils}/bin/wc


set -e
set -u
$MKFIFO alice
$MKFIFO bob

sleep 99999 > alice &
sleep 99999 > bob &

OUT_ALICE=$($MKTEMP)
OUT_BOB=$($MKTEMP)
OUT_DIRSERVER=$($MKTEMP)

echo "Starting services..."

$DIRSERVER &>$OUT_DIRSERVER &
DIRSERVER_PID=$!

$CHATCLIENT --user "alice" <alice &>$OUT_ALICE &
ALICE_PID=$!
$CHATCLIENT --user "bob" <bob &>$OUT_BOB &
BOB_PID=$!

echo "Creating Init Keys..."

echo 4 > bob     #New Init Key
echo 1234 > bob

sleep 1

echo 4 > alice     #New Init Key
echo 4321 > alice

sleep 1

echo "Creating group..."
# create group
echo 5 > alice
echo "mygroup" > alice

sleep 1
echo "Adding bob to group..."
# add bob to group
echo 6 >alice
echo -e "mygroup\nbob">alice

sleep 2

echo "Pulling messages..."
# pull updates
echo 2 > alice
echo 2 > bob

sleep 2

echo "Sending app message from alice to bob..."
# write something
echo 1 > alice
echo -e "mygroup\nhello world">alice

sleep 2

echo "Pulling app message..."
# pull updates
echo 2 > alice
echo 2 > bob

echo "Sending app message from bob to alice..."
# write something
echo 1 > bob
echo -e "mygroup\nhello alice">bob

sleep 2

echo "Pulling app message..."
# pull updates
echo 2 > alice
echo 2 > bob

sleep 2

echo "Alice updates keys ..."
echo 7 > alice
echo -e "mygroup">alice

sleep 2

echo "Pulling messages..."
# pull updates
echo 2 > alice
echo 2 > bob

sleep 2

echo "Checking that the processes still live ..."
kill -0 $BOB_PID
kill -0 $ALICE_PID

echo "Terminating clients..."
# terminate both clients
echo 99 > bob
echo 99 > alice

sleep 2

# check if anything on the serverside went downhill
echo "Checking for server errors ..."
BAD_LOG_COUNT=$(cat $OUT_DIRSERVER | $GREP '\"(POST|GET) \/.*\" (4|5)\d\d' | $WC -l)
if [ "0" != "$BAD_LOG_COUNT" ]
  then
    echo "Something failed server-side"
    exit -1
fi

wait $BOB_PID
wait $ALICE_PID

sleep 2 # Give the FS some time to persist logs

ALICE_MSG_COUNT=$(cat $OUT_ALICE | $GREP -M 'Received Message in Group mygroup:\nhello world' | $WC -l)

if [ "2" != "$ALICE_MSG_COUNT" ]
  then
    echo "Alice message failed, count $ALICE_MSG_COUNT"
    exit -1
fi


BOB_MSG_COUNT=$(cat $OUT_BOB | $GREP -M 'Received Message in Group mygroup:\nhello world' | $WC -l)
if [ "2" != "$BOB_MSG_COUNT" ]
  then
    echo "Bob message failed, count $BOB_MSG_COUNT"
    exit -1
fi

''


