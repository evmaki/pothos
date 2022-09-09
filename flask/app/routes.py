from app import app

import os
from flask import Flask, request, jsonify, send_from_directory
from markupsafe import escape
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import bcrypt
import logging

import settings

app.config['UPLOAD_FOLDER'] = settings.UPLOAD_FOLDER    # directory for uploads
app.config['MAX_CONTENT_LENGTH'] = 8 * 1000 * 1000      # limit files to 8 MB

hashed_password = settings.UPLOAD_PASSWORD_HASHED

def upload(request, valid_extension, output_dir):
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

    # check that filename is valid
    if f.filename == '' or valid_extension not in f.filename:
        logging.warning(f'[{now}] Attempted upload with correct password but invalid file = {f.filename}')
        return jsonify(success=False), 400
    
    # process the file
    if f:
        logging.info(f'[{now}] Successfully uploaded {f.filename}')
        filename = secure_filename(f.filename)
        f.save(os.path.join(f'{app.config["UPLOAD_FOLDER"]}/{output_dir}', filename))
        return jsonify(success=True), 200

@app.route('/api/videos/<video>', methods=['GET', 'POST'])
def videos(video):
    # respond to empty GET with the list of available videos
    if request.method == 'GET' and video == '':
        videos = [f for f in os.listdir(f"{app.config['UPLOAD_FOLDER']}/videos") if '.mp4' in f]
        videos.sort()
    
        return jsonify(videos=videos), 200

    # otherwise respond with the specific video
    elif request.method == 'GET':
        return send_from_directory(f'{app.config["UPLOAD_FOLDER"]}/videos', video)
    
    # process a POST as a video upload
    elif request.method == 'POST':
        return upload(request, '.mp4', 'videos')

@app.route('/api/frames/<frame>', methods=['GET', 'POST'])
def frames(frame):
    # respond to empty GET with list of available frames
    if request.method == 'GET' and escape(frame) == '':
        frames = [f for f in os.listdir(f"{app.config['UPLOAD_FOLDER']}/frames") if '.jpg' in f]
        frames.sort()

        return jsonify(frames=frames), 200

    # otherwise respond with the specific frame
    elif request.method == 'GET':
        return send_from_directory(f'{app.config["UPLOAD_FOLDER"]}/frames', frame)

    # process POST as an upload
    elif request.method == 'POST':
        return upload(request, '.jpg', 'frames')

@app.route('/', methods=['GET'])
@app.route('/latest/', methods=['GET'])
def latest():
    # grab all of the videos and sort in ascending order so we can return the last one
    videos = [f for f in os.listdir(f"{app.config['UPLOAD_FOLDER']}/videos") if '.mp4' in f]
    videos.sort()

    return send_from_directory(f'{app.config["UPLOAD_FOLDER"]}/videos', videos[-1])