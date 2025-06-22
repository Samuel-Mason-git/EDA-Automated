from flask import Flask, render_template, session
from datetime import datetime

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "dev-preview"  # avoid missing secret_key error

@app.route("/app")
def upload_file():
    session['upload_complete'] = True  # mock upload to trigger full nav
    return render_template('upload.html', year=datetime.now().year, max_file_size=15, website_nav=True)

@app.route("/")
def landing():
    from datetime import datetime
    return render_template("landing.html", year=datetime.now().year, website_nav=True, max_file_size=15)

@app.route("/process")
def how_it_works():
    from datetime import datetime
    return render_template("how_it_works.html", year=datetime.now().year, website_nav=True)

@app.route("/about")
def about():
    from datetime import datetime
    return render_template("about.html", year=datetime.now().year, website_nav=True)

@app.route("/example")
def try_example():
    return render_template(
        "index.html",
        year=datetime.now().year,
        overview={},  # or mock some session data if needed
    )

if __name__ == "__main__":
    app.run(debug=True, port=5050)