#!/bin/bash

STORE="boo"

for file in $STORE/*; do
  c=$(echo $file | sed -e 's/'$STORE'\/exp_superdesk_\(.*\).json/\1/')
  mongoimport --db superdesk --collection $c --file $file
done