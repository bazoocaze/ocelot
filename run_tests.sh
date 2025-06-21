#!/bin/bash -x

pipenv -q run coverage erase && pipenv -q run coverage run -m unittest discover -s tests && pipenv -q run coverage report --include="src/*" --brief
