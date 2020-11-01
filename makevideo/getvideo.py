"""動画情報を取得する"""
import os
from datetime import datetime, timedelta
import json

def get_channel_videos(channel: dict, dtdelta) -> list:
    """特定チャンネルの動画リストを取得する"""
    video_list_path = 'data/videolist/' + channel['Name'] + '.json'
    dt_now = datetime.now()
    dt_start = dt_now - dtdelta
    video_list = []
    with open(video_list_path, 'r', encoding='utf-8_sig') as file:
        videoinfo_dict = json.load(file)
    for video in videoinfo_dict.values():
        dt_video = datetime.strptime(video['Published'], "%Y-%m-%dT%H:%M:%S+00:00")
        if dt_video >= dt_start:
            video_list.append(video)
        else:
            pass
    return video_list

def get_group_videos(channel_list: list) -> list:
    """グループ全体の動画リストを取得する"""
    video_list = []
    for channel in channel_list:
        video_list_path = 'data/videolist/' + channel['Name'] + '.json'
        dt_now = datetime.now()
        dt_start = dt_now - timedelta(days=1)
        with open(video_list_path, 'r', encoding='utf-8_sig') as file:
            videoinfo_dict = json.load(file)
        for video in videoinfo_dict:
            dt_video = datetime.strptime(videoinfo_dict[video]['Published'], "%Y-%m-%dT%H:%M:%S+00:00")
            if dt_video >= dt_start:
                video_list.append(video)
            else:
                pass
    return video_list

def download_video(section_list: list, name: str) -> list:
    """セクションリストにある動画をダウンロードする"""
    videopath_list = []
    os.makedirs('data/basevideo/' + name, exist_ok=True)
    for section in section_list:
        videourl = 'https://www.youtube.com/watch?v=' + section['VideoId']
        videopath = 'data/basevideo/' + name + '/' + section['VideoId'] + '.mp4'
        videopath_list.append(videopath)
        if not os.path.exists(videopath):
            runcmd = os.system('youtube-dl '+videourl+' -o '+videopath + ' -f mp4')
            print(runcmd)
    return videopath_list
