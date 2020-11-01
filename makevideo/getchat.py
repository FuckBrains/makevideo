"""youtubeのアーカイブ動画からチャットを取得する"""
import sys
import os
import json
from typing import Union
import traceback
from bs4 import BeautifulSoup
import requests
from retry import retry

class ContinuationURLNotFound(Exception):
    """ContinuationURLNotFound"""

class LiveChatReplayDisabled(Exception):
    """LiveChatReplayDisabled"""

def __get_ytinitialdata(target_url, session) -> dict:
    headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) \
                AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
    html = session.get(target_url, headers=headers)
    soup = BeautifulSoup(html.text, 'html.parser')

    result = {}
    for script in soup.find_all('script'):
        script_text = str(script)
        if 'ytInitialData' in script_text:
            for line in script_text.splitlines():
                if 'ytInitialData' in line:
                    result = json.loads(line.strip()[len('window["ytInitialData"] = '):-1])
                    return result

def __get_continuation(yiinitialdata):
    continuation = yiinitialdata['continuationContents']['liveChatContinuation']['continuations']\
                                [0].get('liveChatReplayContinuationData', {}).get('continuation')
    return continuation

def __check_livechat_replay_disable(yiinitialdata) -> bool:
    twocolumnwatchnextresults = yiinitialdata['contents']['twoColumnWatchNextResults']
    if 'conversationBar' in twocolumnwatchnextresults:
        conversationbarrenderer = twocolumnwatchnextresults['conversationBar'].get('conversationBarRenderer', {})
        if conversationbarrenderer:
            result = bool(conversationbarrenderer['availabilityMessage']\
                            ['messageRenderer']['text']['runs'][0]['text']\
                    == 'この動画ではチャットのリプレイを利用できません。')
        else:
            result = False
    else:
        result = False
    return result

@retry(ContinuationURLNotFound, tries=3, delay=1)
def __get_initial_continuation(target_url, session):

    yiinitialdata = __get_ytinitialdata(target_url, session)

    if __check_livechat_replay_disable(yiinitialdata):
        print("LiveChat Replay is disable")
        raise LiveChatReplayDisabled

    continue_dict = {}
    twocolumnwatchnextresults = yiinitialdata['contents']['twoColumnWatchNextResults']
    if not 'conversationBar' in twocolumnwatchnextresults:
        raise ContinuationURLNotFound

    continuations = twocolumnwatchnextresults['conversationBar']\
                                ['liveChatRenderer']['header']['liveChatHeaderRenderer']\
                                ['viewSelector']['sortFilterSubMenuRenderer']['subMenuItems']
    for continuation in continuations:
        continue_dict[continuation['title']] = \
            continuation['continuation']['reloadContinuationData']['continuation']

    continue_url = continue_dict.get('Live chat repalay')
    if not continue_url:
        continue_url = continue_dict.get('上位のチャットのリプレイ')

    if not continue_url:
        continue_url = continue_dict.get('チャットのリプレイ')

    if not continue_url:
        continue_url = yiinitialdata["contents"]["twoColumnWatchNextResults"]\
                                    ["conversationBar"]["liveChatRenderer"]["continuations"]\
                                    [0].get("reloadContinuationData", {}).get("continuation")

    if not continue_url:
        raise ContinuationURLNotFound

    return continue_url

def __convert_chatreplay(renderer):
    chatlog = {}

    chatlog['user'] = renderer['authorName']['simpleText']
    chatlog['timestampUsec'] = renderer['timestampUsec']
    chatlog['time'] = renderer['timestampText']['simpleText']

    if 'authorBadges' in renderer:
        chatlog['authorbadge'] = renderer['authorBadges'][0]\
                                            ['liveChatAuthorBadgeRenderer']['tooltip']
    else:
        chatlog['authorbadge'] = ""

    content = ""
    if 'message' in renderer:
        if 'simpleText' in renderer['message']:
            content = renderer['message']['simpleText']
        elif 'runs' in renderer['message']:
            for runs in renderer['message']['runs']:
                if 'text' in runs:
                    content += runs['text']
                if 'emoji' in runs:
                    content += runs['emoji']['shortcuts'][0]
    chatlog['text'] = content

    if 'purchaseAmountText' in renderer:
        chatlog['purchaseAmount'] = renderer['purchaseAmountText']['simpleText']
        chatlog['type'] = 'SUPERCHAT'
    else:
        chatlog['purchaseAmount'] = ""
        chatlog['type'] = 'NORMALCHAT'

    return chatlog

def main(videoid, name) -> Union[str, bool]:
    """youtubeのアーカイブ動画からチャットを取得する"""
    youtube_url = "https://www.youtube.com/watch?v="
    target_url = youtube_url + videoid
    continuation_prefix = "https://www.youtube.com/live_chat_replay?continuation="
    chatloglist = []
    session = requests.Session()
    continuation = ""

    try:
        continuation = __get_initial_continuation(target_url, session)
    except LiveChatReplayDisabled:
        print(videoid + " is disabled Livechat replay")
        print(traceback.format_exc())
        return '', False
    except ContinuationURLNotFound:
        print(videoid + " can not find continuation url")
        print(traceback.format_exc())
        return '', False
    except Exception:
        print("video id: " + videoid)
        print("Unexpected error:" + str(sys.exc_info()[0]))
        print(traceback.format_exc())
        return '', False

    count = 1
    result = True
    while True:
        if not continuation:
            break

        try:
            yiinitialdata = __get_ytinitialdata(continuation_prefix + continuation, session)
            if not yiinitialdata:
                print("video id: " + videoid)
                print("is not archive")
                result = False
                break
            continuationcontents = yiinitialdata['continuationContents']
            livechatcontinuation = continuationcontents['liveChatContinuation']
            if not 'actions' in livechatcontinuation:
                break
            for action in yiinitialdata['continuationContents']['liveChatContinuation']['actions']:
                if not 'addChatItemAction' in action['replayChatItemAction']['actions'][0]:
                    continue
                chatlog = {}
                item = action['replayChatItemAction']['actions'][0]['addChatItemAction']['item']
                if 'liveChatTextMessageRenderer' in item:
                    chatlog = __convert_chatreplay(item['liveChatTextMessageRenderer'])
                elif 'liveChatPaidMessageRenderer' in item:
                    chatlog = __convert_chatreplay(item['liveChatPaidMessageRenderer'])
                elif 'liveChatMembershipItemRenderer' in item:
                    chatlog = __convert_chatreplay(item['liveChatMembershipItemRenderer'])
                elif 'liveChatViewerEngagementMessageRenderer' in item:
                    break

                if 'liveChatTextMessageRenderer' in item or 'liveChatPaidMessageRenderer' in item:
                    chatlog['video_id'] = videoid
                    chatlog['Chat_No'] = ("%05d" % count)
                    chatloglist.append(chatlog)
                    count += 1

            continuation = __get_continuation(yiinitialdata)
        except requests.ConnectionError:
            print("Connection Error")
            print(traceback.format_exc())
            result = False
            continue
        except requests.HTTPError:
            print("HTTPError")
            print(traceback.format_exc())
            result = False
            break
        except requests.Timeout:
            print("Timeout")
            print(traceback.format_exc())
            result = False
            continue
        except requests.exceptions.RequestException as exc:
            print(exc)
            print(traceback.format_exc())
            result = False
            break
        except KeyError as exc:
            print("KeyError")
            print(exc)
            print(traceback.format_exc())
            result = False
            break
        except SyntaxError as exc:
            print("SyntaxError")
            print(exc)
            print(traceback.format_exc())
            result = False
            break
        except KeyboardInterrupt:
            print(traceback.format_exc())
            result = False
            break
        except Exception as exc:
            print("video id: " + videoid)
            print("Unexpected error:" + str(sys.exc_info()[0]))
            print(exc)
            print(traceback.format_exc())
            result = False
            break

    if result:
        os.makedirs('data/chat/' + name, exist_ok=True)
        chatfile = 'data/chat/' + name + '/' + videoid + ".json"
        with open(chatfile, "w", encoding="utf-8_sig") as file:
            # print(chat, file=f)
            json.dump(chatloglist, file, ensure_ascii=False, indent=4)

        return chatfile, True
    return '', False
