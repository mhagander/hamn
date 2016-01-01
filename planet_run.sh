#!/bin/sh

cd /home/planetpg/planet
date >> planet.log

if [ -L virtualenv_activate ]; then
    # If there is a link to a virtualenv present, activate that virtualenv before running
    source virtualenv_activate
fi
python aggregator.py >> planet.log 2>&1
python generator.py >>planet.log 2>&1
python posttotwitter.py >>planet.log 2>&1
echo Done `date` >> planet.log
