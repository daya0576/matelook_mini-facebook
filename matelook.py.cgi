#!/usr/bin/env python3.5

from wsgiref.handlers import CGIHandler
from matelook.matelook import app

CGIHandler().run(app)