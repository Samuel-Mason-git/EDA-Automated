def periodic_cleanup(UPLOAD_FOLDER, session_path):
    from maintenance import wipe_all_files_in_folder
    print("🔁 Scheduled cleanup running...")
    wipe_all_files_in_folder(UPLOAD_FOLDER, max_age_minutes=60)
    wipe_all_files_in_folder(session_path, max_age_minutes=60)