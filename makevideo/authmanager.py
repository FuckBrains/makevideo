"""クォータ使用量を管理する"""
from datetime import datetime, timedelta

class AuthManager():
    """認証管理"""
    def __init__(self, ):
        self.__quota_usage = 0
        self.__lock = False
        self.__lock_date = ''
        self.__authinfo_dict = {
            '0': {
                'serviceAccount': 'MyProject-2728-38acdf7414ab.json',
                'oAuth': r'C:\work\makevideo\auth\oauth\client_secrets_0.json',
                'developerKey': 'AIzaSyC7reicu1f4R3BeKA3Vp_OKA3Q116guzyM'},
            '1': {
                'serviceAccount': 'MyProject-2728-38acdf7414ab.json',
                'oAuth': r'C:\work\makevideo\auth\oauth\client_secrets_1.json',
                'developerKey': 'AIzaSyBxMI9AVcZS2TTd-dEKwFvJo14Dlf9-pL8'},
            '2': {
                'serviceAccount': 'MyProject-2728-38acdf7414ab.json',
                'oAuth': r'C:\work\makevideo\auth\oauth\client_secrets_2.json',
                'developerKey': 'AIzaSyCOqp2CD7yy7g3EQ0o3fVOsyRWQ4ld2_js'},
            '3': {
                'serviceAccount': 'MyProject-2728-38acdf7414ab.json',
                'oAuth': r'C:\work\makevideo\auth\oauth\client_secrets_3.json',
                'developerKey': 'AIzaSyDHVyN_LzZgJSYJF0gWUMLkYKa4DGAElBs'},
            '4': {
                'serviceAccount': 'MyProject-2728-38acdf7414ab.json',
                'oAuth': r'C:\work\makevideo\auth\oauth\client_secrets_4.json',
                'developerKey': 'AIzaSyAv7vYeHKEP_aKbsdHBjbLsP1AFTCO5LsM'}
        }
        self.__auth_info_num = 0
        self.__max_usage = 9000

    def __lock_process(self):
        self.__lock = True
        self.__lock_date = datetime.now()

    def switch_auth(self):
        if self.__auth_info_num < 4:
            self.__auth_info_num += 1
        else:
            self.__auth_info_num = 0
            self.__lock_process()

    def __unlock_process(self):
        self.__lock = False
        self.__lock_date = ''

    def use_quota(self, usage: int):
        """クォータを使用する"""
        self.__quota_usage += usage
        if self.__quota_usage >= self.__max_usage:
            self.switch_auth()

    def judge_unlock(self) -> bool:
        """ロック解除するか判断する"""
        if self.__lock:
            delta = datetime.now() - self.__lock_date
            if  delta > timedelta(days=1):
                self.__unlock_process()
        return self.__lock

    def get_auth_info(self) -> dict:
        """認証情報を取得する"""
        return self.__authinfo_dict[str(self.__auth_info_num)]
