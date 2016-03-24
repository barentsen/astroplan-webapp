#!/usr/bin/env python
"""Starts the Flask app in debug mode.

Do not use this in production!
"""
from astroplanapp import app

if __name__ == "__main__":
    app.debug = True
    app.run(port=8080, host='0.0.0.0', debug=True)
