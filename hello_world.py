
from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return """<html>
<head>
<title>Hello world</title>
<meta name="google-site-verification" content="weuweiruoe_google_thing_goes_here_ejkhewejrh" />
</head>
<body>
<h1>
HI EVERYBODY
</h1>
</body>
</html>"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
