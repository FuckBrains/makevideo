"""動画を編集する"""
import os
from datetime import date
import shutil
import cv2
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw
import numpy as np

def combine_video(section_list: list, name: str) -> str:
    """動画を抜粋して結合する"""
    videoclippath_list = []
    os.makedirs('data/videoclip/' + name, exist_ok=True)
    for section in section_list:
        videopath = 'data/basevideo/' + name + '/' + section['VideoId'] + '.mp4'
        videoclippath = 'data/videoclip/' + name + '/' + section['VideoId']\
                        + '_' + section['StartTime'] + '-' + section['EndTime'] + '.mp4'
        ffmpeg_extract_subclip(videopath,
                               int(section['StartTime'])-120,
                               int(section['EndTime'])+20,
                               targetname=videoclippath)
        videoclippath_list.append(videoclippath)
    tempdir = 'data/video/' + name + '/temp/'
    os.makedirs(tempdir, exist_ok=True)
    d_today = date.today()
    newvideopath = 'data/video/' + name + '/' + d_today.strftime('%Y-%m-%d') + '.mp4'
    video = cv2.VideoCapture(videoclippath_list[0])
    framecount = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(video.get(cv2.CAP_PROP_FPS))
    i = 0
    combinecmd = 'ffmpeg'
    for videoclippath in videoclippath_list:
        newvideoclippath = tempdir + os.path.basename(videoclippath)
        if i == 0:
            fadecmd = 'ffmpeg -i ' + videoclippath\
                         +' -vf "fade=out:' + str(framecount - fps) + ':' + str(fps) + '" '\
                         + newvideoclippath
        else:
            fadecmd = 'ffmpeg -i ' + videoclippath\
                         + ' -vf "fade=in:0:' + str(fps) + ','\
                         +' -vf "fade=out:' + str(framecount - fps) + ':' + str(fps) + '" '\
                         + newvideoclippath
        runfadecmd = os.system(fadecmd)
        combinecmd += ' -i ' + newvideoclippath
    combinecmd += ' -filter_complex "concat=n=' + str(len(videoclippath_list)) + ':v=1:a=1" ' + newvideopath
    runcombinecmd = os.system(combinecmd)
    shutil.rmtree(tempdir)
    return newvideopath

def __str2image(fontpath: str, text: str, text_path: str, color):
    font = ImageFont.truetype(fontpath, 200, encoding='utf-8')
    width, hight = font.getsize(text)
    img = Image.new('RGBA', (width, hight))
    draw = ImageDraw.Draw(img)
    draw.font = ImageFont.truetype(fontpath, 200)
    pos = (np.array(img.size) - np.array(draw.font.getsize(text))) / 2.
    borderwidth = 9
    draw.text(pos-(-borderwidth, -borderwidth), text, 'white')
    draw.text(pos-(-borderwidth, +borderwidth), text, 'white')
    draw.text(pos-(+borderwidth, -borderwidth), text, 'white')
    draw.text(pos-(+borderwidth, +borderwidth), text, 'white')
    draw.text(pos, text, color)
    img = img.resize((800, (800*hight)//width), Image.ANTIALIAS)
    img.save(text_path)

def __save_frame_sec(video_path, sec, result_path):
    cap = cv2.VideoCapture(video_path)
    os.makedirs(os.path.dirname(result_path), exist_ok=True)
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.set(cv2.CAP_PROP_POS_FRAMES, round(fps * sec))
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(result_path, frame)

def __paste_image(name_png_path, text_png_path, thumbnail_base_path, thumbnail_path):
    baseimage = Image.open(thumbnail_base_path)
    fontimage1 = Image.open(name_png_path)
    fontimage2 = Image.open(text_png_path)
    back_im = baseimage.copy()
    fontimage_size2 = np.array(fontimage2.size)
    back_im.paste(fontimage1, (50, 0), fontimage1)
    back_im.paste(fontimage2, (50, fontimage_size2[1]), fontimage2)
    back_im.save(thumbnail_path)

def make_thumbnail(section: str, videopath: str, name: str, text: str) -> str:
    """サムネイル画像を作成する"""
    bestmoment = int(section['StartTime']) + (int(section['EndTime']) - int(section['StartTime']))
    # サムネイルディレクトリを設定
    tempdir = 'data/thumbnail/' + name + '/temp/'
    d_today = date.today()
    temppath = tempdir + d_today.strftime('%Y-%m-%d') + '.png'
    __save_frame_sec(videopath, bestmoment, temppath)
    fontpath = r'C:\Users\Yasuhiro Matsutomo\Downloads\AkazukinPOP2\AkazukinPOP2\AkazukiPOP.otf'
    color = (237, 92, 96)
    text = u'今週の見どころ'
    name_png_path = tempdir + '/textimage_' + name + '.png'
    text_png_path = tempdir + '/textimage_' + text + '.png'
    __str2image(fontpath, name, name_png_path, color)
    __str2image(fontpath, text, text_png_path, color)
    # 画像を重ねる
    tumbnaildir = 'data/thumbnail/' + name + '/'
    os.makedirs(tumbnaildir, exist_ok=True)
    thumbnail_path = tumbnaildir + d_today + '.png'
    __paste_image(name_png_path, text_png_path, temppath, thumbnail_path)
    return thumbnail_path

def make_metadata(name: str, text: str, videoid_list: list, channelname: str, channelid: str, dtdelta) -> dict:
    d_today = date.today()
    d_startday = d_today - dtdelta
    metadata_dict = {}
    metadata_dict['title'] = '【' + text + '】' + name + '(' + d_startday.strftime('%y/%m/%d')\
                             + '～' + d_today.strftime('%m/%d') + ')'
    metadata_dict['keywords'] = ''
    metadata_dict['category'] = 'Entertainment'
    video_url = ''
    for videoid in videoid_list:
        video_url += 'https://www.youtube.com/watch?v=' + videoid + '\r\n'
    if channelid:
        channel_url = '#' + channelname + '\r\n'\
                        'https://www.youtube.com/channel/' + channelid + '\r\n'
    else:
        channel_url = ''
    metadata_dict['description'] = '#ホロライブ\r\n'\
                                    + 'https://www.youtube.com/channel/UCJFZiqLMntJufDCHc6bQixg' + '\r\n'\
                                    + channel_url\
                                    + '引用元動画\r\n'\
                                    + video_url
    return metadata_dict
