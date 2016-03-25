"""Implements the astroplan-based sky target visibility web tool using Flask.
"""
import matplotlib
matplotlib.use('agg')
from matplotlib import pyplot as pl

import flask
import json

from astropy import units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord
from astropy.utils.data import get_file_contents

import astroplan
from astroplan.plots import plot_altitude

try:
    from io import BytesIO  # Python 3
except ImportError:
    from cStringIO import StringIO as BytesIO  # Legacy Python


app = flask.Flask('astroplanapp')


def observing_sites():
    """Returns a dict of observatory sites based on astropy's database."""
    jsonurl = 'http://data.astropy.org/coordinates/sites.json'
    js = json.loads(get_file_contents(jsonurl, show_progress=False, cache=True))
    sitedict = {}
    for sitekey, site in js.items():
        sitedict[sitekey] = site['name']
    return sitedict


def _parse_single_target(target):
    try:
        crd = SkyCoord(target)
    except ValueError:  # The coordinate string is ambiguous; make assumptions
        if target[0].isalpha():
            crd = SkyCoord.from_name(target)
        elif ":" in target:
            crd = SkyCoord(target, unit="hour,deg")
        else:
            crd = SkyCoord(target, unit="deg")
    return astroplan.FixedTarget(crd)


def _parse_targets(targets):
    """Parses the 'targets' GET argument.

    Returns
    -------
    targets : list of `astropy.FixedTarget` objects
    """
    if targets is None:
        return []
    result = [_parse_single_target(single_target)
              for single_target in targets.splitlines()]
    return result


@app.route('/')
def root():
    return flask.render_template('index.html', sites=observing_sites())


@app.route('/plot-airmass')
def app_plot_airmass():
    date = flask.request.args.get('date', default=None, type=str)
    location = flask.request.args.get('location', default=None, type=str)
    targets = flask.request.args.get('targets', default=None, type=str)
    targets = targets.replace("\n", "%0A").replace("\r", "%0D")
    return flask.render_template('airmass.html', date=date, location=location, targets=targets)


@app.route('/airmass.png')
def airmass_png():
    # Parse the arguments
    date = flask.request.args.get('date', default=None, type=str)
    location = flask.request.args.get('location', default=None, type=str)
    targets = flask.request.args.get('targets', default=None, type=str)
    observer = astroplan.Observer.at_site(location)
    if date is None:
        midnight = observer.midnight(Time.now())
    else:
        # +10*u.minute circumvents astroplan issue #155
        midnight = observer.midnight(Time(date)) + 10 * u.minute
    targets = _parse_targets(targets)
    # Create the airmass plot
    fig = pl.figure()
    ax = fig.add_subplot(111)
    for target in targets:
        plot_altitude(target, observer, midnight, ax=ax)
    pl.tight_layout()
    # Stream the image to the browser using BytesIO
    img = BytesIO()
    fig.savefig(img, transparent=True, format='png')
    img.seek(0)
    response = flask.send_file(img, mimetype="image/png")
    return response
