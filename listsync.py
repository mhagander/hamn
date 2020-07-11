#!/usr/bin/env python3
"""Planet PostgreSQL - list synchronizer

This file contains the functions to synchronize the list of subscribers
to planet with those of a pglister mailinglist.

Copyright (C) 2008-2017 PostgreSQL Global Development Group
"""

import sys
import configparser
import psycopg2
import requests


if __name__ == "__main__":
    c = configparser.ConfigParser()
    c.read('planet.ini')

    conn = psycopg2.connect(c.get('planet', 'db'))
    curs = conn.cursor()
    curs.execute("""
SELECT DISTINCT email FROM auth_user
INNER JOIN feeds ON auth_user.id=feeds.user_id
WHERE feeds.approved AND NOT feeds.archived
""")
    syncstruct = [{'email': r[0]} for r in curs.fetchall()]

    r = requests.put(
        '{0}/api/subscribers/{1}/'.format(c.get('list', 'server'), c.get('list', 'listname')),
        headers={'X-api-key': c.get('list', 'apikey')},
        json=syncstruct,
    )
    if r.status_code != 200:
        print("Failed to talk to pglister api: %s" % r.status_code)
        print(r.text)
        sys.exit(1)

    j = r.json()
    for a in j['added']:
        print("Added subscriber %s" % a)
    for a in j['deleted']:
        print("Removed subscriber %s" % a)
