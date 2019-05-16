#!/bin/bash
export PATH="$coreutils/bin"

mkdir -p ./out/dirserver
mkdir -p ./out/integration_tests

cp -r $dirserver/* ./out/dirserver
cp -r $integration_test/* ./out/integration_tests

mkdir -p $out
cp -r ./out/* $out