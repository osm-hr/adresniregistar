#!/usr/bin/env python3
"""
Gets the gf_download_oauth cookie from Geofabrik internal server
by logging in with OSM username and password.

Usage:
    python3 get_geofabrik_cookie.py <osm_username> <osm_password>

Output:
    Prints the cookie value to stdout, suitable for use in scripts:
    export GEOFABRIK_OAUTH_COOKIE=$(python3 src/get_geofabrik_cookie.py user pass)
"""

import sys
import requests
from bs4 import BeautifulSoup


def get_geofabrik_cookie(username, password):
    session = requests.Session()
    session.headers['User-Agent'] = 'Mozilla/5.0 (compatible; geofabrik-cookie-fetcher)'

    # Step 1: Hit Geofabrik internal → redirects to OSM OAuth
    resp = session.get('https://osm-internal.download.geofabrik.de/?landing_page=true', allow_redirects=False)
    if resp.status_code not in (301, 302, 303):
        raise Exception(f"Expected redirect from Geofabrik, got {resp.status_code}")

    osm_oauth_url = resp.headers['Location']

    # Step 2: Follow to OSM OAuth page (may redirect to login first)
    resp = session.get(osm_oauth_url, allow_redirects=True)

    # Step 3: If redirected to login page, log in
    if '/login' in resp.url:
        soup = BeautifulSoup(resp.text, 'html.parser')
        csrf_input = soup.find('input', {'name': 'authenticity_token'})
        if not csrf_input:
            raise Exception("Could not find CSRF token on OSM login page")
        csrf = csrf_input['value']

        resp = session.post('https://www.openstreetmap.org/login', data={
            'username': username,
            'password': password,
            'authenticity_token': csrf,
            'referer': osm_oauth_url,
            'commit': 'Login',
        }, allow_redirects=True)

        if '/login' in resp.url:
            raise Exception("Login failed — check username and password")

    # Step 4: Submit OAuth authorization form
    soup = BeautifulSoup(resp.text, 'html.parser')
    form = soup.find('form')
    if form:
        form_data = {}
        for inp in form.find_all('input'):
            if inp.get('name'):
                form_data[inp['name']] = inp.get('value', '')
        form_data['commit'] = 'Authorize'

        action = form.get('action') or resp.url
        if action.startswith('/'):
            action = 'https://www.openstreetmap.org' + action

        resp = session.post(action, data=form_data, allow_redirects=True)

    # Step 5: Extract cookie
    for cookie in session.cookies:
        if cookie.name == 'gf_download_oauth':
            return cookie.value

    raise Exception("gf_download_oauth cookie not found after auth flow")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <osm_username> <osm_password>", file=sys.stderr)
        sys.exit(1)

    username, password = sys.argv[1], sys.argv[2]
    try:
        cookie = get_geofabrik_cookie(username, password)
        print(cookie)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
