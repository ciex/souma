import os

from web_ui import app
from flask import session
from datetime import datetime
from gevent import sleep


# For calculating scores
epoch = datetime.utcfromtimestamp(0)
epoch_seconds = lambda dt: (dt - epoch).total_seconds() - 1356048000


def score(star_object):
    import random
    return random.random() * 100 - random.random() * 10


def get_active_persona():
    from nucleus.models import Persona
    """ Return the currently active persona or 0 if there is no controlled persona. """

    if 'active_persona' not in session or session['active_persona'] is None:
        controlled_personas = Persona.query.filter('sign_private != ""')

        if controlled_personas.first() is None:
            return ""
        else:
            session['active_persona'] = controlled_personas.first().id

    return session['active_persona']


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


def watch_layouts(continuous=True):
    """Watch layout file and update layout definitions once they change

    Parameters:
        continuous (bool): Set False to only load definitions once

    Returns:
        dict: Layout definitions if `continuous` is False
    """
    import json

    mtime_last = 0
    layout_filename = os.path.join(app.config["RUNTIME_DIR"], 'static', 'layouts.json')
    cont = True
    while cont is True:
        mtime_cur = os.path.getmtime(layout_filename)

        if mtime_cur != mtime_last:
            try:
                with open(layout_filename) as f:
                    app.config['LAYOUT_DEFINITIONS'] = json.load(f)
            except IOError:
                app.logger.error("Failed loading layout definitions")
                app.config['LAYOUT_DEFINITIONS'] = dict()
            else:
                app.logger.info("Loaded {} layout definitions".format(len(app.config["LAYOUT_DEFINITIONS"])))
        mtime_last = mtime_cur

        cont = True if continuous is True else False
        sleep(1)

    return app.config["LAYOUT_DEFINITIONS"]
