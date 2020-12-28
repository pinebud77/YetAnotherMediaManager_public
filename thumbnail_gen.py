#!/usr/bin/env python3


import io
from PIL import Image
from moviepy.editor import *


MIN_IMAGE_COUNT = 5
MAX_IMAGE_COUNT = 30
DEF_THUMBNAIL_SIZE = 360
DEF_STREAM_PERIOD = 90


def get_resize(max_val, width, height):
    if width >= height:
        return (max_val, int(height / width * max_val))
    else:
        return (int(width / height * max_val), max_val)


def create_thumbnails(fpath, period=DEF_STREAM_PERIOD, size=DEF_THUMBNAIL_SIZE):
    clip = VideoFileClip(fpath)

    if clip.duration < period * MIN_IMAGE_COUNT:
        period = clip.duration / MIN_IMAGE_COUNT
    if clip.duration > period * MAX_IMAGE_COUNT:
        period = clip.duration / MAX_IMAGE_COUNT

    resize = get_resize(size, clip.size[0], clip.size[1])

    duration = int(clip.duration)
    if duration == 0:
        duration = 1

    period = int(period)
    if period == 0:
        period = 1

    thumbnails = []
    for time in range(0, duration, period):
        frame = clip.get_frame(time)
        p = Image.fromarray(frame)
        p.thumbnail((size, size))

        byte_arr = io.BytesIO()
        p.save(byte_arr, format='JPEG')

        thumbnails.append((time, byte_arr.getvalue()))

    return thumbnails


if __name__ == '__main__':
    thumbnails = create_thumbnails('\\\\192.168.25.25\\administrator\\tt\\.t\\Administrator\\Recycled\\heydouga\\ARISA2.wmv')

    fileno = 0
    for thumbnail in thumbnails:
        f = open('test%2.2d.jpg' % fileno, 'wb')
        f.write(thumbnail[1])
        f.close()
        fileno += 1




