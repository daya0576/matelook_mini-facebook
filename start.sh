#!/usr/bin/env bash

uwsgi --http 0.0.0.0:5005 --master --processes 4 -w matelook_mini-facebook.matelook:app