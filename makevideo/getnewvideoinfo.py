""" Webスクレイピングを行うモジュール """
import os
import json
import pathlib
import feedparser
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import baseinfo

import authmanager

def __get_videoinfo(entries: list, channel: dict) -> dict:
    videoinfo = {}
    for entry in entries:
        videoinfo['ChannelId'] = entry.yt_channelid
        videoinfo['VideoId'] = entry.yt_videoid
        videoinfo['Title'] = entry.title
        videoinfo['Published'] = entry.published
        videoinfo['Summary'] = entry.published
        videoinfo['Name'] = channel['Name']
        break
    return videoinfo

def __isvideopost(videoinfo: dict, channel: dict) -> bool:
    isposted = False
    video_list_path = 'data/videolist/' + channel['Name'] + '.json'
    videoinfo_dict = {}
    if not os.path.exists(video_list_path):
        isposted = True
        emptyfile = pathlib.Path(video_list_path)
        emptyfile.touch()
    else:
        with open(video_list_path, 'r', encoding='utf-8_sig') as file:
            videoinfo_dict = json.load(file)
            max_key = len(videoinfo_dict)-1
            if max_key >= 2:
                min_key = max_key-2
            else:
                min_key = -1
            for key in range(max_key, min_key, -1):
                if videoinfo['VideoId'] == videoinfo_dict[str(key)]['VideoId']:
                    break
                isposted = True
    if isposted:
        videoinfo_dict[len(videoinfo_dict)] = videoinfo
        with open(video_list_path, 'w', encoding='utf-8_sig') as file:
            json.dump(videoinfo_dict, file, ensure_ascii=False, indent=4)
    else:
        pass
    return isposted

def main() -> list:
    """動画投稿を検知する"""
    channel_list = baseinfo.get_channellist()
    videoinfo_list = []
    os.makedirs('data/videolist/', exist_ok=True)
    for channel in channel_list:
        mls_rdf = 'https://www.youtube.com/feeds/videos.xml?channel_id=' + channel['ChannelId']
        mls_dic = feedparser.parse(mls_rdf)
        videoinfo = __get_videoinfo(mls_dic.entries, channel)
        if __isvideopost(videoinfo, channel):
            videoinfo_list.append(videoinfo)
        else:
            pass
    return videoinfo_list

def get_allvideos(channelid: str, name: str, youtube_api_key: str) -> dict:
    """特定チャンネルのすべての動画情報を取得する"""
    youtube = build('youtube', 'v3', developerKey=youtube_api_key)
    video_list_path = 'data/videolist/' + name + '.json'
    videoinfo = {}
    videoinfo_list = []
    videoinfo_dict = {}
    videoid_list = []
    # next_pagetoken = ''
    pagetoken = ''
    authmanagerobj = authmanager.AuthManager()
    while True:
        # if not next_pagetoken:
            # pagetoken = next_pagetoken
        try:
            search_response = youtube.search().list(
                part="snippet",
                channelId=channelid,
                maxResults=10,
                order="date" #日付順にソート
            ).execute()
        except HttpError as e:
            if e.resp.status == 403:
                authmanagerobj.switch_auth()
                authinfo_dict = authmanagerobj.get_auth_info()
                youtube = build('youtube', 'v3', developerKey=authinfo_dict['developerKey'])
                search_response = youtube.search().list(
                    part="snippet",
                    channelId=channelid,
                    maxResults=50,
                    order="date" #日付順にソート
                ).execute()
            else:
                raise
        for search_result in search_response.get("items", []):
            if search_result["id"]["kind"] == "youtube#video":
                videoid_list.append(search_result["id"]["videoId"])
        if 'nextPageToken' in search_response:
            next_pagetoken = search_response["nextPageToken"]
        else:
            break
    for videoid in videoid_list:
        video_response = youtube.videos().list(
            part='snippet,statistics',
            id=videoid
        ).execute()
        for video_result in video_response.get("items", []):
            if video_result["kind"] == "youtube#video":
                videoinfo['ChannelId'] = channelid
                videoinfo['VideoId'] = videoid
                videoinfo['Title'] = video_result["snippet"]["title"]
                videoinfo['Published'] = video_result["snippet"]["publishedAt"]
                videoinfo['Name'] = name
                videoinfo_list.insert(0, videoinfo)
    video_num = 0
    for videoinfo in videoinfo_list:
        videoinfo_dict[video_num] = videoinfo
        video_num += 1
    if os.path.exists(video_list_path):
        with open(video_list_path, 'w', encoding='utf-8_sig') as file:
            json.dump(videoinfo_dict, file, ensure_ascii=False, indent=4)
    return videoinfo_dict
