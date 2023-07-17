#!/bin/bash

home=`realpath $(dirname $0)`
cd $home

python3 -m unittest discover -s ./tests -p test_*.py