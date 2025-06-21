#!/bin/bash -x

pipenv -q run python -m unittest discover -s tests

