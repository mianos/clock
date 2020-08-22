#!/usr/bin/env python
from gevent import monkey
monkey.patch_all(subprocess=True)
import arrow
import requests
import re
import logging

from influxdb import InfluxDBClient

import gevent
from gevent.pywsgi import WSGIServer


from flask import Flask, render_template, jsonify, g
from bs4 import BeautifulSoup

# from flask.logging import default_handler


class YourFlask(Flask):
    def create_jinja_environment(self):
        self.config['TEMPLATES_AUTO_RELOAD'] = True
        return Flask.create_jinja_environment(self)

def timer():
    while True:
        gevent.sleep(10)

# gevent.spawn(timer)
app = YourFlask(__name__)
app.config['DEBUG'] = False
#app.logger.removeHandler(default_handler)

iclient = InfluxDBClient(host='mqtt2.mianos.com', port=8086)
iclient.switch_database('radiation')


@app.route('/')
def hello_world():
    return render_template('clock.html')


last_request = arrow.Arrow.min
wdata = None
pm25 = 0

@app.route('/time')
def time():
    global last_request, wdata, pm25

    now = arrow.now()
    timestr = now.format('h:mm')
    if now.second % 2:
        tt = timestr.replace(':', '.')
    else:
            tt = timestr
    if (now - last_request).seconds > 60 * 15:
        wdata = requests.get("http://rss.weatherzone.com.au/?u=12994-1285&lt=aploc&lc=624&obs=1&fc=1").text
        aa = iclient.query('select last(datetime),pm25  from environment group by *');
        pm25 = aa.raw['series'][0]['values'][0][2]
        last_request = now

    items = BeautifulSoup(wdata, 'html.parser').findAll('item')
    def clean(aa):
        return BeautifulSoup(aa.description.contents[0], 'html.parser').text.replace('\r', '').split('\n')
    temp = clean(items[0])
    forecast = clean(items[1])
    temp_line = "<strong>%s</strong>      <small>(%s)</small>" % (re.match("Temperature: (.*)$", temp[1]).groups()[0], re.match("Feels like: (.*)$", temp[4]).groups()[0])
    forecast_line = ' '.join(forecast[3:5])
    return jsonify(time=tt,
                   date="%s (sk %s)" % (now.strftime('%d %b'), arrow.now("Europe/Bratislava").format("h:mma")),
                   temp=temp_line,
                   forecast=forecast_line,
                   pm25="pm25: %d" % pm25)



if __name__ == '__main__':
    # http_server = wsgi.WSGIServer(('', 5000), app, log=None).serve_forever()
    http_server = WSGIServer(('', 5000), app, log=None).serve_forever()
