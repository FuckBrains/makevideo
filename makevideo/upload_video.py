"""動画をアップロードする"""
import os
import random
import sys
import time
import argparse
import http.client  # httplibはPython3はhttp.clientへ移行
import httplib2

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow

def __init(auth_info):
    # 再試行の対象とするapiclient.errors.HttpErrorのステータスコード
    httplib2.RETRIES = 1

    # 最大再試行回数
    global MAX_RETRIES
    MAX_RETRIES = 10

    # 再試行の対象とする例外
    global RETRIABLE_EXCEPTIONS
    RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error,
                            IOError,
                            http.client.NotConnected,
                            http.client.IncompleteRead,
                            http.client.ImproperConnectionState,
                            http.client.CannotSendRequest,
                            http.client.CannotSendHeader,
                            http.client.ResponseNotReady,
                            http.client.BadStatusLine)

    # 再試行の対象とするapiclient.errors.HttpErrorのステータスコード
    global RETRIABLE_STATUS_CODES
    RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

    # OAuth 2.0情報を含むファイルを指定
    global CLIENT_SECRETS_FILE
    CLIENT_SECRETS_FILE = auth_info['oAuth']

    # Youtubeへのアップロードを許可
    global YOUTUBE_UPLOAD_SCOPE
    YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
    global YOUTUBE_API_SERVICE_NAME
    YOUTUBE_API_SERVICE_NAME = "youtube"
    global YOUTUBE_API_VERSION
    YOUTUBE_API_VERSION = "v3"

    # CLIENT_SECRETS_FILEがない場合のメッセージ.
    global MISSING_CLIENT_SECRETS_MESSAGE
    MISSING_CLIENT_SECRETS_MESSAGE = """
    WARNING: Please configure OAuth 2.0

    To make this sample run you will need to populate the client_secrets.json file
    found at:

    %s

    with information from the API Console
    https://console.developers.google.com/

    For more information about the client_secrets.json file format, please visit:
    https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
    """ % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       CLIENT_SECRETS_FILE))

    global VALID_PRIVACY_STATUSES
    VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

def __get_authenticated_service(args):
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
                                   scope=YOUTUBE_UPLOAD_SCOPE,
                                   message=MISSING_CLIENT_SECRETS_MESSAGE)

    storage = Storage("%s-oauth2.json" % sys.argv[0])
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, args)

    return build(YOUTUBE_API_SERVICE_NAME,
                 YOUTUBE_API_VERSION,
                 http=credentials.authorize(httplib2.Http()))

def __upload_thumbnail(youtube, video_id, file):
    youtube.thumbnails().set(
        videoId=video_id,
        media_body=file
    ).execute()

def __initialize_upload(youtube, options):
    tags = None
    if options.keywords:
        tags = options.keywords.split(",")

    body = dict(
        snippet=dict(
            title=options.title,
            description=options.description,
            tags=tags,
            categoryId=options.category
        ),
        status=dict(
            privacyStatus=options.privacyStatus
        )
    )

  # Call the API's videos.insert method to create and upload the video.
    insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        # The chunksize parameter specifies the size of each chunk of data, in
        # bytes, that will be uploaded at a time. Set a higher value for
        # reliable connections as fewer chunks lead to faster uploads. Set a lower
        # value for better recovery on less reliable connections.
        #
        # Setting "chunksize" equal to -1 in the code below means that the entire
        # file will be uploaded in a single HTTP request. (If the upload fails,
        # it will still be retried where it left off.) This is usually a best
        # practice, but if you're using Python older than 2.6 or if you're
        # running on App Engine, you should set the chunksize to something like
        # 1024 * 1024 (1 megabyte).
        media_body=MediaFileUpload(options.file, chunksize=-1, resumable=True)
    )

    return __resumable_upload(insert_request)

# This method implements an exponential backoff strategy to resume a
# failed upload.
def __resumable_upload(insert_request):
    response = None
    error = None
    retry = 0
    while response is None:
        try:
            print("Uploading file...")
            status, response = insert_request.next_chunk()
            if response is not None:
                if 'id' in response:
                    print("Video id '%s' was successfully uploaded." % response['id'])
                else:
                    exit("The upload failed with an unexpected response: %s" % response)
        except HttpError as exc:
            if exc.resp.status in RETRIABLE_STATUS_CODES:
                error = "A retriable HTTP error %d occurred:\n%s" % \
                        (exc.resp.status, exc.content)
            else:
                raise
        except RETRIABLE_EXCEPTIONS as exc:
            error = "A retriable error occurred: %s" % exc
        if error is not None:
            print(error)
            retry += 1
            if retry > MAX_RETRIES:
                exit("No longer attempting to retry.")
            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print("Sleeping %f seconds and then retrying..." % sleep_seconds)
            time.sleep(sleep_seconds)
    return response['id']

def __uploadthumbnail(youtube, video_id, thumbnailpath):
    if not os.path.exists(thumbnailpath):
        exit("Please specify a valid file using the --file= parameter.")

    try:
        __upload_thumbnail(youtube, video_id, thumbnailpath)
    except HttpError as exc:
        print("An HTTP error %d occurred:\n%s" % (exc.resp.status, exc.content))
    else:
        print("The custom thumbnail was successfully set.")

def main(videopath, thumbnailpath, metadata, auth_info):
    """動画をアップロードする"""
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    args = parser.parse_args()
    args.file = videopath
    args.title = metadata['title']
    args.keywords = metadata['keywords']
    args.category = metadata['category']
    args.description = metadata['description']
    args.privacyStatus = 'unlisted'
    #args.privacyStatus = 'public'
    args.auth_info = auth_info
    args.auth_host_name = 'localhost'
    args.auth_host_port = [8080, 8090]
    args.logging_level = 'ERROR'
    args.noauth_local_webserver = False

    __init(args.auth_info)

    if not os.path.exists(args.file):
        exit("Please specify a valid file using the --file= parameter.")

    youtube = __get_authenticated_service(args)
    try:
        video_id = __initialize_upload(youtube, args)
        __uploadthumbnail(youtube, video_id, thumbnailpath)
    except HttpError as exc:
        print("An HTTP error %d occurred:\n%s" % (exc.resp.status, exc.content))
