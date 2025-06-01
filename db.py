import os
import psycopg2
from flask import request
import logging 

DATABASE_URL = os.environ['DATABASE_URL']

def log_upload(filename, size_mb, duration_sec):
    logging.basicConfig(level=logging.INFO)
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO upload_logs (filename, file_size_mb, processing_duration_sec, ip, user_agent)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    filename,
                    size_mb,
                    duration_sec,
                    request.remote_addr,
                    request.headers.get('User-Agent')
                ))
                print("✅ Upload logged to Supabase")
                logging.info("✅ Upload sent to Supabase")
    except Exception as e:
        print("Upload logging failed:", e)
        logging.error(f"❌ Failed to log upload to Supabase: {e}")

def save_feedback(rating, feedback):
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO feedback_reviews (rating, feedback)
                    VALUES (%s, %s)
                """, (rating, feedback))
                print("✅ Upload logged to Supabase")
                logging.info("✅ Upload sent to Supabase")
    except Exception as e:
        print("Feedback logging failed:", e)
        logging.error(f"❌ Failed to log upload to Supabase: {e}")
