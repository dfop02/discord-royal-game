import re
from pytube import YouTube

async def valid_yt_link(link):
    if not valid_link(link):
        return (False, 'Invalid youtube video link, please try again.')

    yt = YouTube(link)
    if yt.length > 240:
        return (False, 'Video must be less than 4 minutes long, try again.')

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
