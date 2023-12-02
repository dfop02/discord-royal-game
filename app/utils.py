import re
import io
import cv2
import requests
import numpy as np
from datetime import datetime
from pytube import YouTube
from app.music.player import extract_video_id_by_url

async def valid_yt_link(link):
    max_video_length = 180

    if not valid_link(link):
        return (False, 'Invalid youtube video link, please try again.')

    yt = YouTube(link)
    if yt.length > max_video_length:
        return (False, f'Video must be less than {secs_to_MS(max_video_length)} minutes long, try again.')

    try:
        yt.check_availability()
    except Exception as error:
        print(error)
    else:
        return (True, '')

def valid_link(link):
    regex = r"^(https?\:\/\/)?((www\.)?youtube\.com|youtu\.be)\/.+$"
    url = re.findall(regex, link)
    return url[0] if url else False

async def clear_last_msg(ctx, n_msgs=1):
    await ctx.channel.purge(limit=n_msgs, check=lambda msg: not msg.pinned)

async def print_thumbnail(ctx, url):
    img = get_thumbnail(url)
    await ctx.send(file=discord.File(io.BytesIO(img), 'anime.jpg'))

async def print_current_match(ctx, bracket):
    await ctx.send(f'Match => {bracket[0][0]} VS {bracket[1][0]}')

    img1 = get_thumbnail(bracket[0][1])
    img2 = get_thumbnail(bracket[1][1])
    img_merged = cv2.hconcat([img1, img2])

    text = 'VS'
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_size = 1.5
    font_stroke = 3

    text_width, text_height = cv2.getTextSize(text, font, font_size, font_stroke+2)[0]
    position = ((int) (img_merged.shape[1]/2 - text_width/2), (int) (img_merged.shape[0]/2 + text_height/2))
    cv2.putText(img_merged,text,position,font,font_size,(0,0,0),font_stroke+2)
    cv2.putText(img_merged,text,position,font,font_size,(195,136,59),font_stroke)

    font_size = 1

    cv2.rectangle(img_merged, (0, img_merged.shape[0]-50), (50, img_merged.shape[0]), (195,136,59), -1)
    cv2.putText(img_merged,'A',(15, img_merged.shape[0]-15),font,font_size,(255, 255, 255),font_stroke)

    cv2.rectangle(img_merged, (img_merged.shape[1]-50, img_merged.shape[0]-50), (img_merged.shape[1], img_merged.shape[0]), (195,136,59), -1)
    cv2.putText(img_merged,'B',(img_merged.shape[1]-35, img_merged.shape[0]-15),font,font_size,(255, 255, 255),font_stroke)

    # JPEG quality, 0 - 100
    jpeg_quality = 95
    _, final_img = cv2.imencode('.jpeg', img_merged, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
    await ctx.send(file=discord.File(io.BytesIO(final_img), 'imgvsimg.jpg'))

def get_thumbnail(url, readFlag=cv2.IMREAD_COLOR):
    resp = requests.get(f'http://img.youtube.com/vi/{extract_video_id_by_url(url)}/0.jpg')
    image = np.asarray(bytearray(resp.content), dtype=np.uint8)
    image = cv2.imdecode(image, readFlag)
    return image

def secs_to_MS(secs):
    return datetime.fromtimestamp(secs).strftime('%M:%S')
