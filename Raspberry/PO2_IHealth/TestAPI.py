
from flask import Flask, redirect
from iHealthClass import iHealth

app = Flask(__name__)
api = iHealth()


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/authorize')
def authorize():
    r = api.authorize()
    if type(r) is str:
        return r
    else:
        return redirect(r.url)


@app.route('/callback')
def callback():
    r = api.callback()
    return r


@app.route('/api_blood_oxygen')
def api_blood_oxygen():
    r = api.get_blood_oxygen(0)
    return str(r)

@app.route('/api_blood_oxygen_30')
def api_blood_oxygen_30():
    r = api.get_blood_oxygen(30)
    return str(r)


if __name__ == '__main__':
    app.run(debug=True)
