""" analyse video """
import json
import collections
import re
import os
import numpy
from collections import deque

def __extract_funnytext(chatloglist: list) -> dict:
    chattexts = []
    chattimes = []
    starttime = chatloglist[0]['timestampUsec']
    for chatlog in chatloglist:
        chattexts.append(chatlog['text'])
        chattimes.append(int(chatlog['timestampUsec']) - int(starttime))
    index = 0
    chat = {'text': [], 'time': []}
    for text in chattexts:
        index = index + 1
        result = re.search(
            '(w(?![a-zA-Z])|'
            '(?![a-zA-Z])w|'
            'W(?![a-zA-Z])|'
            '(?![a-zA-Z])W|'
            'ｗ|笑|草|蔦|茶葉)',
            text)
        if not result:
            continue
        chat['text'].append(text)
        chat['time'].append(chattimes[index - 1] // 1000000)
    return chat

def __score_funnypoint(chat: dict, videoid: str, name: str) -> None:
    time_counter = collections.Counter(chat['time'])
    time_counter = sorted(time_counter.items())

    point_dict = dict()
    interval = 100
    period = interval
    point = 0
    for record in time_counter:
        time, counter = record
        if time <= period:
            point += counter
        else:
            point_dict[str(period - interval) + "-" + str(period)] = point
            period = period + interval
            point = counter

    os.makedirs('data/funnypoint/' + name, exist_ok=True)
    funnypoint_path = 'data/funnypoint/' + name + '/' + videoid + '.json'
    with open(funnypoint_path, 'w', encoding='utf-8_sig') as file:
        json.dump(point_dict, file, ensure_ascii=False, indent=4)

def score_video(chatpath: str, videoid: str, name: str) -> None:
    """採点"""
    with open(chatpath, 'r', encoding='utf-8_sig') as file:
        chatloglist = json.load(file)
        chat = __extract_funnytext(chatloglist)
        __score_funnypoint(chat, videoid, name)

def __sort_multisectionpoint(videoid, score_dict, section_num) -> dict:
    score = {}
    score_deque = deque()
    multiscore_dict = {}
    for timerange, point in score_dict.items():
        score[timerange] = point
        score_deque.append(score)
        if len(score_deque) < 5:
            pass
        else:
            score_deque.popleft()
            l = list(score_deque)
            multiscore_dict[timerange] = sum([d.values() for d in l])
    multiscore_list = sorted(multiscore_dict.items(), reverse=True, key=lambda x:x[1])
    topscore_dict = {}
    section_count = 0
    for timerange, point in multiscore_list:
        if section_count < section_num:
            starttime, endtime = timerange.split("-")
            for i in range(section_num):
                score_dict[str(int(starttime)-(20*i))\
                       +'-'+str(int(endtime)-(20*i))]
            np.std(x)
            # 標準偏差算出
            # 平均値算出
            # 和
            # 和以上となった時間を求める
            # 和未満となった時間を求める
            # start-30
            # end+10
            # topscore_dictに追加
            
            
            topscore_dict[videoid + '/' + timerange] = point # 中央時間を入れる
            section_count += 1
        else:
            break
    return topscore_dict

def extract_section(scoredfile_list: list, section_number: int) -> list:
    """評価ファイルリストから、section_number位までの抜粋区間を選択する"""
    topscore_dict = {}
    allscore_dict = {}
    for scoredfile in scoredfile_list:
        videoid = os.path.splitext(os.path.basename(scoredfile))[0]
        with open(scoredfile, 'r', encoding='utf-8_sig') as file:
            score_dict = json.load(file)
        topscore_dict = __sort_multisectionpoint(videoid, score_dict, 5)
        allscore_dict.update(topscore_dict)
    allscore_list = sorted(allscore_dict.items(), reverse=True, key=lambda x:x[1])
    section = {}
    section_list = []
    section_count = 0
    for key, point in allscore_list:
        if section_count < section_number:
            videoid, timekey = key.split("/")
            starttime, endtime = timekey.split("-")
            section = {'VideoId':videoid,
                       'StartTime':starttime,
                       'EndTime':endtime}
            section_list.append(section)
            section_count += 1
        else:
            break
    return section_list
