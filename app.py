from flask import Flask, render_template
import requests
from bs4 import BeautifulSoup
from collections import namedtuple
import datetime
from dateutil.parser import parse
import geocoder


def parse_date(date_str):
    return parse(date_str
                 .replace('Last updated: ', '')
                 .replace(' (Central Standard Time)', ''))


CallForService = namedtuple('CallForService',
                            ('time', 'number', 'address', 'reason'))


def cached(func):
    memo = {}

    def cached_version():
        if 'result' not in memo or (
                datetime.datetime.now() - memo['last_updated'] >
                datetime.timedelta(minutes=10)
        ):
            memo['result'] = func()
            memo['last_updated'] = parse_date(memo['result']['last_updated'])
        return memo['result']
    return cached_version


@cached
def calls_for_service():
    resp = requests.get('http://www.slmpd.org/cfs.aspx')
    soup = BeautifulSoup(resp.text)
    return dict(
        markers=map(marker_from_call, current_calls(soup)),
        last_updated=last_updated(soup)
    )


def last_updated(soup):
    return soup.find(id='lblLastUpdate').text


def current_calls(soup):
    return [CallForService(*[td.text for td in tr.find_all('td')])
            for tr in soup.find_all('tr')]


def marker_from_call(call):
    g = geocoder.google(location_str(call.address))
    return dict(
        lat=g.lat,
        lng=g.lng,
        address=call.address,
        reason=call.reason,
        time=call.time)


def location_str(address):
    return '{} St. Louis, MO'.format(
        address.replace('/', '&').replace('XX', '00'))

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html', **calls_for_service())

if __name__ == '__main__':
    app.run(debug=True)
