#!/bin/bash

cd /opt/superdesk/ &&
python3 -m venv env && . env/bin/activate && pip install -Ur dev-requirements.txt && . activate.sh && nosetests