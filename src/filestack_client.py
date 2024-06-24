import os
import requests
from base64 import b64encode
from dotenv import load_dotenv

load_dotenv()

FILESTACK_USER_NAME = os.environ.get('FILESTACK_USER_NAME')
FILESTACK_PASSWORD = os.environ.get('FILESTACK_PASSWORD')
FILESTACK_ENDPOINT = os.environ.get('FILESTACK_ENDPOINT')

class FilestackClient():
    def get_filestack_app_detail(self, dev_id,auth_email):
        response = self.executeAPI('apps?developer_id='+str(dev_id),'get',None,auth_email)
        return response

    def filestack_login(self, filestack_email,filestack_password):
        payload = {'email':filestack_email,'password':filestack_password}
        response = self.executeAPI('developer/login','post',payload,filestack_email)
        return response

    def executeAPI(self, api_name,method_type,payload,auth_email):
        base_url = FILESTACK_ENDPOINT
        auth_username = FILESTACK_USER_NAME
        auth_password = FILESTACK_PASSWORD
        auth_token = b64encode(f"{auth_username}:{auth_password}".encode('utf-8')).decode("ascii")
        # headers = {}
        # if auth_email:
        headers = { 'Authorization' : f'Basic {auth_token}', 'Content-Type': "application/json", 'Accept': "application/json", "X-Auth-Email":auth_email }
        # else:
        #     headers = { 'Authorization' : f'Basic {auth_token}', 'Content-Type': "application/json", 'Accept': "application/json" }
        api_url = base_url + api_name
        print(f"api_url:{api_url},headers:{headers}, Payload:{payload}" )
        if method_type == 'post':
            response = requests.post(api_url, headers=headers, json=payload)
            print(response)
            return response.json()
        elif method_type == 'get':
            response = requests.get(api_url, headers=headers)
            return response.json()