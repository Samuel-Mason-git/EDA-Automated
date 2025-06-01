from data_quality import load_dataframe, data_quality_check, overview, data_quality_recommendations
from maintenance import convert_numpy, wipe_all_files_in_folder
from scheduler import periodic_cleanup
from db import log_upload, save_feedback
from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session
import json
from datetime import datetime
import numpy as np
import tempfile
import os
import time
from waitress import serve
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import psycopg2

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")
DATABASE_URL = os.getenv("DATABASE_URL")
flask_files_route = os.path.join(os.getcwd(), 'flask_files')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(flask_files_route, 'flask_session')
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024
max_file_size = 200 * 1024 * 1024
Session(app)
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
scheduler = BackgroundScheduler()
scheduler.add_job(lambda: periodic_cleanup(UPLOAD_FOLDER, app.config['SESSION_FILE_DIR']), 'interval', minutes=1)
scheduler.start()
atexit.register(lambda: scheduler.shutdown(wait=False))

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    print(f"📩 Request method: {request.method}")
    if request.method == 'POST':
        file = request.files.get('file')
        print(f"📁 File received: {file.filename if file else 'None'}")
        if file:
            total_start = time.time()
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            timers = {}

            load_start = time.time()
            df = load_dataframe(file_path)
            timers['load_dataframe'] = time.time() - load_start
            print(f"✅ Dataframe loaded in {time.time() - load_start:.2f} seconds")

            quality_start = time.time()
            data_quality = data_quality_check(df)
            timers['data_quality'] = time.time() - quality_start
            print(f"✅ Data Quality completed in {time.time() - quality_start:.2f} seconds")

            overview_start = time.time()
            overview_data = overview(df, data_quality)
            timers['overview'] = time.time() - overview_start
            print(f"✅ Overview generated in {time.time() - overview_start:.2f} seconds")

            recs = time.time()
            data_quality_recs = data_quality_recommendations(df, overview_data, data_quality)
            timers['checklist'] = time.time() - recs
            print(f"✅ Recommendations calculated and generated in {time.time() - recs:.2f} seconds")

            caching = time.time()
            session['overview'] = convert_numpy(overview_data)
            session['data_quality'] = convert_numpy(data_quality)
            session['data_quality_recs'] = convert_numpy(data_quality_recs)
            timers['caching'] = time.time() - caching
            print(f"✅ Caching completed in {time.time() - caching:.2f} seconds")

            try:
                os.remove(file_path)
                print(f"🧹 Removed uploaded file from disk: {file_path}")
            except Exception as e:
                print(f"⚠️ Could not delete uploaded file: {e}")

            end = time.time()
            duration = end - total_start
            speed = file_size_mb / duration
            print(f"[Benchmark] Processed {file_size_mb:.2f} MB in {duration:.2f} seconds — {speed:.2f} MB/s")
            print("⏱️ Stage timings:")
            for k, v in timers.items():
                print(f"  {k}: {v:.2f} sec")

            session['upload_complete'] = True
            log_upload(file.filename, file_size_mb, duration)

            session['uploaded_file'] = file_path
            return redirect(url_for('index'))
        else:
            print("❌ No file uploaded — reloading upload screen.")
    return render_template('upload.html', year=datetime.now().year, hide_navbar=True, max_file_size=max_file_size)

@app.route('/overview')
def index():
    if 'overview' not in session:
        print("🚫 Upload not complete or cache missing — redirecting.")
        return redirect(url_for('upload_file'))
    
    #session.pop('upload_complete', None)
    print("✅ Showing dataset overview page.")
    return render_template('index.html', 
                           overview=session['overview'], 
                           year=datetime.now().year)


@app.route('/datatype-analysis')
def datatype_analysis():    
    if 'data_quality' not in session:
        return redirect(url_for('upload_file'))
    return render_template('datatype_analysis.html',
                           data_quality=session['data_quality'],
                           year=datetime.now().year)


@app.route('/data-quality-checklist')
def data_quality_checklist():
    if 'data_quality_recs' not in session:
        return redirect(url_for('upload_file'))
    return render_template('data_quality_checklist.html',
                           data_quality_recommendations=session['data_quality_recs'],
                           year=datetime.now().year)

@app.route('/clear')
def clear_dataset():
    file_path = session.get('uploaded_file')
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
    session.clear()
    print("🧹 Dataset cleared and session reset.")
    return redirect(url_for('upload_file'))

@app.route('/submit-review', methods=['POST'])
def submit_review():
    data = request.get_json()
    feedback = data.get('feedback_text', '').strip()
    rating = data.get('rating', '').strip()

    if feedback and rating:
        try:
            save_feedback(rating, feedback)  # 👈 write to Supabase
            print("✅ Review saved to Supabase.")
            return {'status': 'success'}, 200
        except Exception as e:
            print("❌ Failed to save review:", e)
            return {'status': 'error', 'message': 'Failed to save review'}, 500
    else:
        return {'status': 'error', 'message': 'Missing fields'}, 400


if __name__ == '__main__':
    print("🔁 Cleaning old files...")
    wipe_all_files_in_folder(UPLOAD_FOLDER)
    wipe_all_files_in_folder(app.config['SESSION_FILE_DIR'])
    print("✅ Cleanup complete. Starting server.")
    serve(app, host='127.0.0.1', port=8000, max_request_body_size=10 * 1024 * 1024 * 1024)


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404