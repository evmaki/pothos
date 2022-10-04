from app import app

import os, json
from flask import Flask, request, jsonify, send_from_directory
from markupsafe import escape
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import bcrypt
import logging

import settings

app.config['UPLOAD_FOLDER'] = settings.UPLOAD_FOLDER    # directory for uploads
app.config['MAX_CONTENT_LENGTH'] = 32 * 1000 * 1000     # limit files to 32 MB

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

""" Responds to GET with a JSON collection of videos
"""
@app.route('/api/videos', methods=['GET'])
def video_list():
    videos = [f for f in os.listdir(f"{app.config['UPLOAD_FOLDER']}/videos") if '.mp4' in f]
    videos.sort()

    return jsonify(videos=videos), 200

""" Responds to GET with a specific video file
"""
@app.route('/api/videos/<video>', methods=['GET'])
def videos(video):
    return send_from_directory(f'{app.config["UPLOAD_FOLDER"]}/videos', escape(video))

""" Accepts POST with a video and upload password
"""
@app.route('/api/add/video', methods=['POST'])
def video_upload():
    # process a POST as a video upload
    return upload(request, '.mp4', 'videos')

""" Responds to GET with a JSON collection of frames
"""
@app.route('/api/frames', methods=['GET'])
def frame_list():
    frames = [f for f in os.listdir(f"{app.config['UPLOAD_FOLDER']}/frames") if '.jpg' in f]
    frames.sort()

    return jsonify(frames=frames), 200

""" Responds to GET with a specific frame
"""
@app.route('/api/frames/<frame>', methods=['GET'])
def frames(frame):
    return send_from_directory(f'{app.config["UPLOAD_FOLDER"]}/frames', escape(frame))

""" Accepts POST with a frame and upload password
"""
@app.route('/api/add/frame', methods=['POST'])
def frame_upload():
    return upload(request, '.jpg', 'frames')

@app.route('/api/data', methods=['GET'])
def data():
    return send_from_directory(app.config["UPLOAD_FOLDER"], 'data.json')

@app.route('/api/add/data', methods=['POST'])
def data_upload():
    # check the password first
    password = request.form['password'].encode('ascii')

    if not bcrypt.checkpw(password, hashed_password):
        logging.warning(f'[{now}] Attempted data upload with incorrect password = {password}, file = {f.filename}')
        return jsonify(success=False), 401

    f = request.files['file']

    # check for file in POST request
    if 'file' not in request.files:
        logging.warning(f'[{now}] Request with no file included.')
        return jsonify(success=False), 400

    # FIXME this is inefficient
    # separate out the new entries
    with open(os.path.join(app.config["UPLOAD_FOLDER"], 'data.json')) as fp:
        data1 = json.load(fp)
        data2 = json.load(f)

        k1s = set(data1.keys())
        k2s = set(data2.keys())

        new_ks = k2s - k1s

        for k in new_ks:
            data1[k] = data2[k]

        with open(os.path.join(app.config["UPLOAD_FOLDER"], 'data.json'), 'w') as f:
            json.dump(data1, f)

        return jsonify(success=True), 200
    
    return jsonify(success=False), 404

""" Responds to GET with the most recently uploaded video
"""
@app.route('/', methods=['GET'])
@app.route('/latest/', methods=['GET'])
def latest():
    # grab all of the videos and sort in ascending order so we can return the last one
    videos = [f for f in os.listdir(f"{app.config['UPLOAD_FOLDER']}/videos") if '.mp4' in f]
    videos.sort()

    return send_from_directory(f'{app.config["UPLOAD_FOLDER"]}/videos', videos[-1])