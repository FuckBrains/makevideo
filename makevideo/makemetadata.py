def main(originalVideoMetaData: list):
    metadata = dict()
    metadata['title'] = '【笑えるシーン】'+originalVideoMetaData['charactor']+'【'+ originalVideoMetaData['published']+'【放送分】'
    metadata['description'] =   '引用元：\r\n' + \
                                    'https://www.youtube.com/watch?v=' + originalVideoMetaData['video_id'] + '\r\n' + \
                                    '\r\n' + \
                                    '#ホロライブ\r\n' + \
                                    'チャンネル：https://www.youtube.com/channel/UCJFZiqLMntJufDCHc6bQixg' + '\r\n' + \
                                    '\r\n' + \
                                    '#'+originalVideoMetaData['charactor'] + '\r\n' + \
                                    'チャンネル：https://www.youtube.com/channel/' + originalVideoMetaData['channel_id'] + '\r\n'
    metadata['category'] = 'Entertainment'
    metadata['keywords'] = ''
    metadata['privacyStatus'] = 'public'

    return metadata

if __name__ == '__main__':
    import argparse
    # parserを作成
    parser = argparse.ArgumentParser(description="メタデータ作成")
    # 引数を追加
    parser.add_argument('originalVideoMetaData', type=list, nargs='?', default='-', help='元動画メタデータ')
    # 引数を解析
    args = parser.parse_args()
    # main実行
    metadata = main(args.originalVideoMetaData)