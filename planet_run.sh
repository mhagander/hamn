#!/bin/sh

PATH=$PATH:/usr/local/bin

cd /home/planetpg/planet
date >> planet.log
python aggregator.py >> planet.log 2>&1
python generator.py >>planet.log 2>&1
echo Done `date` >> planet.log
