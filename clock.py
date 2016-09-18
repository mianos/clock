import datetime
import requests

from flask import Flask, render_template, jsonify
from bs4 import BeautifulSoup

class YourFlask(Flask):
    def create_jinja_environment(self):
        self.config['TEMPLATES_AUTO_RELOAD'] = True
        return Flask.create_jinja_environment(self)

app = YourFlask(__name__)

@app.route('/')
def hello_world():
    return render_template('clock.html')


last_request = datetime.datetime(datetime.MINYEAR, 1, 1)
wdata = None

@app.route('/time')
def time():
    global last_request, wdata

    now = datetime.datetime.now()
    timestr = now.strftime('%l:%M')
    if now.second % 2:
        tt = timestr.replace(':', '.')
    else:
            tt = timestr
    if (now - last_request).seconds > 60 * 15:
        print "request"
        wdata = requests.get("http://rss.weatherzone.com.au/?u=12994-1285&lt=aploc&lc=624&obs=1&fc=1").text
        last_request = now

    items = BeautifulSoup(wdata, 'html.parser').findAll('item')
    def clean(aa):
        return BeautifulSoup(aa.description.contents[0], 'html.parser').text.replace('\r', '').split('\n')
    temp = clean(items[0])
    forecast = clean(items[1])
    temp_line = ' '.join([temp[1], temp[4]])
    forecast_line = ' '.join(forecast[3:5])
    return jsonify(time=tt, date=now.strftime('%d %b'), temp=temp_line, forecast=forecast_line)
