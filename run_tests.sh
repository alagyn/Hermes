#!/bin/bash

home=`realpath $(dirname $0)`
cd $home

cmake --preset default
cmake --build --preset tests
ctest --preset all
