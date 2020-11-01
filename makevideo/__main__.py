""" makevideo main """
# cd C:\work\makevideo\script
# python -m makevideo
# とすれば動く
import time
from datetime import timedelta
import os
import schedule
import getnewvideoinfo
import getchat
import analyzevideo
import baseinfo
import editvideo
import authmanager
import upload_video
import getvideo

def analyse_video():
    """ 動画を分析する """
    # リスト内のチャンネルで動画投稿を検知
    videoinfo_list = getnewvideoinfo.main()
    for videoinfo in videoinfo_list:
        print('投稿:' + videoinfo['Name'])
        # チャット取得
        chatpath, result = getchat.main(videoinfo['VideoId'], videoinfo['Name'])
        if result:
            print('チャット取得成功')
            # 採点
            analyzevideo.score_video(chatpath, videoinfo['VideoId'], videoinfo['Name'])
            print('採点終了')
        else:
            print('チャット取得失敗')

def analyse_all_video():
    """ 過去すべての動画を分析する """
    # リスト内のチャンネル情報を取得
    channel_list = baseinfo.get_channellist()
    for channel in channel_list:
        authinfo_dict = authmanagerobj.get_auth_info()
        name = channel['Name']
        # チャンネル内の動画情報をすべて取得
        videoinfo_dict = getnewvideoinfo.get_allvideos(
            channel['ChannelId'], name, authinfo_dict['developerKey']
            )
        if not videoinfo_dict:
            for videoinfo in videoinfo_dict:
                print('投稿:' + videoinfo['Name'])
                # チャット取得
                chatpath, result = getchat.main(videoinfo['VideoId'], name)
                if result:
                    print('チャット取得成功')
                    # 採点
                    analyzevideo.score_video(chatpath, videoinfo['VideoId'], name)
                    print('採点終了')
                else:
                    print('チャット取得失敗')
        else:
            pass

def __make_video(name: str, channelid: str, video_list: list, text1: str, text2: str, dtdelta):
    # 1週間に投稿された動画の評価ファイルを取得する
    scoredfile_list = []
    for video in video_list:
        scoredfile = 'data/funnypoint/' + video['Name'] + '/' + video['VideoId'] + '.json'
        if os.path.exists(scoredfile):
            scoredfile_list.append(scoredfile)
    # それぞれの評価ファイルから、5位までの抜粋区間を選択する
    section_list = analyzevideo.extract_section(scoredfile_list, 5)
    # 動画ダウンロード
    videopath_list = getvideo.download＿video(section_list, name)
    # 動画編集
    newvideopath = editvideo.combine_video(section_list, name)
    # サムネイル作成
    thumbnailpath = editvideo.make_thumbnail(
        section_list[0], videopath_list[0], text1, text2)
    # VideoIdリストを取得
    videoid_list = [section.get('VideoId') for section in section_list]
    # メタデータ作成
    metadata_dict = editvideo.make_metadata(
        text1, text2, videoid_list, name, channelid, dtdelta)
    # 認証情報切り替え
    auth_info = authmanagerobj.get_auth_info()
    # 動画アップロード
    upload_video.main(newvideopath, thumbnailpath, metadata_dict, auth_info)
    # クォータ使用
    authmanagerobj.use_quota(1600)

def make_group_video():
    """グループの動画を作成する"""
    channel_list = baseinfo.get_channellist()
    video_list = []
    text1 = 'ホロライブ'
    text2 = '今日の見どころ'
    for channel in channel_list:
        # 1日に投稿された動画の情報を取得する
        channel_video_list = getvideo.get_channel_videos(channel, timedelta(days=1))
        video_list.extend(channel_video_list)
    __make_video('ホロライブ', '', video_list, text1, text2, timedelta(days=1))

def __make_channel_video(week: str):
    """単一チャンネルの動画を作成する"""
    if authmanagerobj.judge_unlock():
        return
    channel_list = baseinfo.get_channellist()
    for channel in channel_list:
        if channel['Week'] == week:
            text2 = '今週の見どころ'
            # 1週間に投稿された動画の情報を取得する
            video_list = getvideo.get_channel_videos(channel, timedelta(weeks=1))
            # 動画を作成する
            __make_video(channel['Name'], channel['ChannelId'], video_list, channel['Name'], text2, timedelta(weeks=1))
        else:
            pass

authmanagerobj = authmanager.AuthManager()
#analyse_video()
make_group_video()
# analyse_all_video()
#__make_channel_video('monday')
# 1分毎に動画を分析
schedule.every(1).minutes.do(__analyse_video)
# 1日毎(4:00)にグループの動画を作成
schedule.every().day.at("04:00").do(__make_group_video)
# 1週間毎に単一チャンネルの動画を作成
schedule.every().monday.do(__make_channel_video, week='monday')
schedule.every().tuesday.do(__make_channel_video, week='tuesday')
schedule.every().wednesday.do(__make_channel_video, week='wednesday')
schedule.every().thursday.do(__make_channel_video, week='thursday')
schedule.every().friday.do(__make_channel_video, week='friday')
schedule.every().saturday.do(__make_channel_video, week='saturday')
schedule.every().sunday.do(__make_channel_video, week='sunday')

while True:
    schedule.run_pending()
    time.sleep(1)
