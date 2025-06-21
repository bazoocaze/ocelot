#!/bin/bash -x

pipenv -q run coverage run -m unittest discover -s tests --cover-package=src --cover-erase --cover-brief
