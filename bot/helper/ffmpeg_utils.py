import os
import sys
import json
import time
import ffmpeg
from subprocess import call, check_output
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

def get_codec(filepath, channel='v:0'):
    output = check_output(['ffprobe', '-v', 'error', '-select_streams', channel,
                            '-show_entries', 'stream=codec_name,codec_tag_string', '-of', 
                            'default=nokey=1:noprint_wrappers=1', filepath])
    return output.decode('utf-8').split()

def encode(filepath):
    basefilepath, extension = os.path.splitext(filepath)
    output_filepath = basefilepath + '.HEVC' + '.mp4'
    assert(output_filepath != filepath)
    if os.path.isfile(output_filepath):
        print('Skipping "{}": file already exists'.format(output_filepath))
        return None
    print(filepath)
    # Get the video channel codec
    video_codec = get_codec(filepath, channel='v:0')
    if video_codec == []:
        print('Skipping: no video codec reported')
        return None
    # Video transcode options
    if video_codec[0] == 'hevc':
        if video_codec[1] == 'hvc1':
            print('Skipping: already h265 / hvc1')
            return None
        else:
            # Copy stream to hvc1
            video_opts = '-c:v copy -tag:v hvc1'
    else:
        # Transcode to h265 / hvc1
        video_opts = '-c:v libx265 -color_primaries 1 -color_range 1 -color_trc 1 -colorspace 1 -crf 24.2  -threads 8  -pix_fmt yuv420p -preset slow -profile:v main -vf'
        opt1 = ",".join(['smartblur=1.5:-0.35:-3.5:0.65:0.25:2.0','scale=1280:720:spline16+accurate_rnd+full_chroma_int'])
        opt2 = '-x265-params'
        opt3 = ":".join(['me=2','rd=4','subme=7','aq-mode=3','aq-strength=1','deblock=1,1','psy-rd=1','psy-rdoq=1','rdoq-level=2','merange=32','bframes=8','b-adapt=2','limit-sao=1'])
    # Get the audio channel codec
    audio_codec = get_codec(filepath, channel='a:0')
    if audio_codec == []:
        audio_opts = ''
    elif audio_codec[0] == 'libopus':
        audio_opts = '-c:a copy -c:s copy'
    else:
        audio_opts = '-c:a libopus -b:a 128k'
    #call(['ffmpeg', '-i', filepath] + video_opts.split() + opt1.split() + opt2.split() + opt3.split() + audio_opts.split() + [output_filepath])
    #call(['ffmpeg', '-i', filepath, audio_opts, video_opts , opt1, opt2, opt3, output_filepath])
    call(['ffmpeg', '-i', filepath, '-b:a 128k -c:a libopus -c:v libx265 -color_primaries 1 -color_range 1 -color_trc 1 -colorspace 1 -crf 24.2  -threads 8 -c:s copy  -pix_fmt yuv420p -preset slow -profile:v main -vf smartblur=1.5:-0.35:-3.5:0.65:0.25:2.0,scale=1280:720:spline16+accurate_rnd+full_chroma_int -x265-params me=2:rd=4:subme=7:aq-mode=3:aq-strength=1:deblock=1,1:psy-rd=1:psy-rdoq=1:rdoq-level=2:merange=32:bframes=8:b-adapt=2:limit-sao=1', output_filepath])
    os.remove(filepath)
    return output_filepath

def get_thumbnail(in_filename, path, ttl):
    out_filename = os.path.join(path, str(time.time()) + ".jpg")
    open(out_filename, 'a').close()
    try:
        (
            ffmpeg
            .input(in_filename, ss=ttl)
            .output(out_filename, vframes=1)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        return out_filename
    except ffmpeg.Error as e:
      return None

def get_duration(filepath):
    metadata = extractMetadata(createParser(filepath))
    if metadata.has("duration"):
      return metadata.get('duration').seconds
    else:
      return 0

def get_width_height(filepath):
    metadata = extractMetadata(createParser(filepath))
    if metadata.has("width") and metadata.has("height"):
      return metadata.get("width"), metadata.get("height")
    else:
      return 1280, 720
