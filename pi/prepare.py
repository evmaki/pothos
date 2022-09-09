# takes all the frames in ./frames/, preps them into a video and uploads it
import requests
from datetime import datetime, timedelta
from os import listdir, path, makedirs, rename, popen

from PIL import Image, ImageStat, UnidentifiedImageError, ImageEnhance

# contains API keys, IP addresses, etc
import settings

abs_path = path.abspath(path.dirname(__file__))

upload_url = settings.UPLOAD_URL
upload_password = settings.UPLOAD_PASSWORD

def move_image(input_path, output_dir):
    output_dir = f'{abs_path}/frames/{output_dir}'

    # create the archive directory if it doesn't exist
    if not path.exists(output_dir):
        makedirs(output_dir)

    fn = input_path.split('/')[-1]
    rename(input_path, f'{output_dir}/{fn}')

def prepare_image(input_path, output_dir):
    # try to open the image, and catch the exception if the image file is corrupt
    try: 
        with Image.open(input_path) as im:
            # need to go in 180px on the left for res (1280, 960) and maybe a little on the bottom to hide the bolts in the shelf
            # (left, upper, right, lower)
            im_crop = im.crop((200, 0, 1280, 880))

            # check the image stats to see if it's a dud
            stat = ImageStat.Stat(im_crop)

            # filter out bad frames (light level is bad, washed out and purply, etc) by thresholding the variance in pixel intensity per channel
            threshold = 2000

            if stat.var[0] < threshold or stat.var[1] < threshold or stat.var[2] < threshold:
                # move the dud into the archive
                move_image(input_path, 'archive')
            else:
                im_crop = ImageEnhance.Contrast(im_crop).enhance(1.05)
                
                color_transform = (
                    1, 0,    0, 0, 
                    0, 0.96, 0, 0, 
                    0, 0,    1, 0
                )

                im_out = im_crop.convert('RGB', color_transform)

                fn = input_path.split('/')[-1]
                im_out.save(f'{output_dir}/{fn}')

                print(f'saved image {output_dir}/{fn}')

    except UnidentifiedImageError:
        move_image(input_path, 'archive')

def prepare_frames():
    input_dir = f'{abs_path}/frames'
    output_dir = f'{input_dir}/prepared'

    # find out where ffmpeg is installed in the current environment (assumes which is in /usr/bin)
    ffmpeg_path = popen(f'/usr/bin/which ffmpeg').read()[:-1]  # grab the path and drop the trailing newline

    if not path.exists(output_dir):
        makedirs(output_dir)

    # generate a list of dates from the past week to match to the frames
    today = datetime.now().strftime('%m-%d-%Y')
    past = datetime.now() - timedelta(days=7)
    past = past.strftime('%m-%d-%Y')

    start = datetime.strptime(past, '%m-%d-%Y')
    end = datetime.strptime(today, '%m-%d-%Y')
    dates = [start + timedelta(days=x) for x in range(0, (end-start).days)]

    dates = [date.strftime('%m-%d-%Y') for date in dates]

    # grab all the raw frames from the past week only
    frames = [f for f in [f for f in listdir(input_dir) if '.jpg' in f] if f.split('_')[0] in dates]
    frames.sort()

    prepared_frames = [f for f in listdir(output_dir) if '.jpg' in f]

    # prepare (crop and color balance) the frames if they haven't been prepared already
    for frame in frames:
        if frame not in prepared_frames:
            prepare_image(f'{input_dir}/{frame}', output_dir)

    frame1 = frames[0].split('.')[0]
    framen = frames[-1].split('.')[0]

    output_fn = f'{frame1},{framen}'

    # generate the video if it doesn't exist
    if not path.exists(f'{output_dir}/{output_fn}.mp4'):
        ffmpeg_stream = popen(f'{ffmpeg_path} -framerate 20 -pattern_type glob -i \'{output_dir}/*.jpg\' -c:v libx264 -pix_fmt yuv420p {output_dir}/{output_fn}.mp4')
        ffmpeg_stream.read()
        print(f'saved {output_dir}/{output_fn}.mp4')
    else:
        print(f'output video {output_dir}/{output_fn}.mp4 exists already.')

    # upload the video
    f = open(f'{output_dir}/{output_fn}.mp4', 'rb')
    upload_response = requests.post(upload_url, files={'file': f}, data={'password': upload_password})
    
    if upload_response.status_code != 200:
        print(f'upload failed with status code {upload_response.status_code}')
    else:
        print('uploaded video')

prepare_frames()