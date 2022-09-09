from app import app

import os
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import bcrypt
import logging

import settings

app.config['UPLOAD_FOLDER'] = settings.UPLOAD_FOLDER    # directory for uploads
app.config['MAX_CONTENT_LENGTH'] = 8 * 1000 * 1000      # limit files to 8 MB

hashed_password = settings.UPLOAD_PASSWORD_HASHED

@app.route('/api/upload/', methods=['POST'])
def upload():
    now = datetime.now().strftime('%m-%d-%Y-%H:%M')

    # check for file in POST request
    if 'file' not in request.files:
        logging.warning(f'[{now}] Request with no file included.')
        return jsonify(success=False), 400

    if 'password' not in request.form:
        logging.warning(f'[{now}] Request with no password included.')
        return jsonify(success=False), 401

    password = request.form['password'].encode('ascii')

    if not bcrypt.checkpw(password, hashed_password):
        logging.warning(f'[{now}] Attempted upload with incorrect password = {password}, file = {f.filename}')
        return jsonify(success=False), 401

    f = request.files['file']

    # get yesterday's date (it should be in the filename when updating at midnight, so we'll check)
    date = datetime.now() - timedelta(days=1)
    date = date.strftime('%m-%d-%Y')

    # check that filename is valid
    if f.filename == '' or '.mp4' not in f.filename or date not in f.filename:
        logging.warning(f'[{now}] Attempted upload with correct password but invalid file = {f.filename}')
        return jsonify(success=False), 400
    
    # process the file
    if f:
        logging.info(f'[{now}] Successfully uploaded {f.filename}')
        filename = secure_filename(f.filename)
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify(success=True), 200

@app.route('/', methods=['GET'])
@app.route('/latest/', methods=['GET'])
def latest():
    # grab all of the videos and sort in ascending order so we can return the last one
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if '.mp4' in f]
    files.sort()

    return send_from_directory(app.config['UPLOAD_FOLDER'], files[-1])