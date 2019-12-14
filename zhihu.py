#!/usr/bin/python
# -*- coding : utf-8 -*-

"""                                                   
File: zhihu.py
Author: dwh
E-mail: dwh@bupt.edu.cn
Created: 2019/11/12 20:47
Description:                                              
"""

from hashlib import sha1
from bs4 import BeautifulSoup
from service import MySQLServices
from models import UserInfo, UserInfos, AnswerDetail, AskDetail
from requests.exceptions import ConnectionError
import requests
import re
import execjs
import time
import hmac
import json
import random

proxy_list = [
    'http://59.57.38.81:9999',
    'http://117.28.96.50:9999',
    'http://117.28.96.198:9999',
    'http://27.152.90.142:9999',
    'http://27.152.2.179:9999',
    'http://117.28.96.14:9999',
    'http://27.152.8.232:9999',
    'http://59.57.38.225:9999',
    'http://117.28.97.189:9999',
    'http://27.152.90.6:9999',
    'http://117.28.97.91:9999',
    'http://27.152.91.216:9999',
    'http://117.28.97.119:9999',
    'http://27.152.90.93:9999',
    'http://117.28.97.169:9999',
    'http://27.152.91.155:9999',
    'http://27.152.91.64:9999',
    'http://117.28.96.197:9999',
    'http://27.152.90.54:9999',
    'http://27.152.90.217:9999',
    'http://27.152.91.154:9999',
    'http://117.28.97.147:9999',
    'http://27.152.24.115:9999',
    'http://27.152.91.208:9999',
    'http://117.28.97.147:9999',
    'http://27.152.24.115:9999',
    'http://27.152.91.208:9999',
    'http://117.30.112.93:9999',
    'http://59.57.38.207:9999'
]

def get_random_ip():
    proxy_ip = random.choice(proxy_list)
    proxies = {'http': proxy_ip}
    return proxies

def verify_user(dic):
    if 'uid' in dic.keys():
        return False
    elif dic['name'] == 'kaifulee':
        return False
    else:
        if dic['isOrg'] == True:
            return False
        elif dic['answerCount'] <= 5:
            return False
        else:
            return True

def bulk_users(dic, session):
    for key in dic:
        print(dic[key])
        if verify_user(dic[key]):
            username = dic[key]['name']
            answer = dic[key]['answerCount']
            url = dic[key]['url']
            sex = dic[key]['gender']
            new_user = UserInfo(username=username, answer_num=answer, url=url, sex=sex)
            MySQLServices.insert(session, new_user)
        else:
            continue


class Zhihu(object):

    def __init__(self, username, password):

        self.username = username
        self.password = password
        self.session = requests.session()
        self.headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36',
            'x-zse-83': '3_1.1'
        }
        self.proxy = get_random_ip()

    def login(self):

        # 请求login_url,udid_url,captcha_url加载所需要的cookie
        login_url = 'https://www.zhihu.com/signup?next=/'
        resp = self.session.get(login_url, headers=self.headers, proxies=self.proxy)        
        print("请求{}，响应状态码:{}".format(login_url,resp.status_code)) 

        udid_url = 'https://www.zhihu.com/udid'
        resp = self.session.post(udid_url, headers=self.headers, proxies=self.proxy)
        print("请求{}，响应状态码:{}".format(udid_url,resp.status_code)) 
        # print(self.session.cookies.get_dict())

        captcha_url = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=en'
        resp = self.session.get(captcha_url, headers=self.headers, proxies=self.proxy)
        print("请求{}，响应状态码:{}".format(captcha_url,resp.status_code)) 
        # print(self.session.cookies.get_dict())
        # print(resp.text)
        # self.save_file('captcha',resp.text)
        
        # 校验是否需要验证吗，需要则直接退出，还没遇到过需要验证码的
        if re.search('true',resp.text):
            print('需要验证码')
            exit()
        
        # 获取signature参数
        self.time_str = str(int(time.time()*1000))
        signature = self.get_signature()
        # print(signature)

        # 拼接需要加密的字符串
        string = "client_id=c3cef7c66a1843f8b3a9e6a1e3160e20&grant_type=password&timestamp={}&source=com.zhihu.web&signature={}&username={}&password={}&captcha=&lang=en&ref_source=homepage&utm_source=".format(self.time_str,signature,self.username,self.password)
        # print(string)
        # 加密字符串
        encrypt_string = self.encrypt(string)
        # print(encrypt_string)

        # post请求登陆接口
        post_url = "https://www.zhihu.com/api/v3/oauth/sign_in"
        resp = self.session.post(post_url, data=encrypt_string, headers=self.headers, proxies=self.proxy)
        print("请求{}，响应状态码:{}".format(post_url,resp.status_code)) 
        # print(self.session.cookies.get_dict())
        # print(resp.text)
        # self.save_file('post',resp.text)

        # 校验是否登陆成功
        if re.search('user_id',resp.text):
            print('登陆成功')
        else:
            print("登陆失败")
            exit()

    def test(self):

        # 请求个人信息接口查看个人信息
        me_url = 'https://www.zhihu.com/api/v4/me'
        data = {
            'include': 'ad_type;available_message_types,default_notifications_count,follow_notifications_count,vote_thank_notifications_count,messages_count;draft_count;following_question_count;account_status,is_bind_phone,is_force_renamed,email,renamed_fullname;ad_type'
        }
        resp = self.session.get(me_url, data=data, headers=self.headers, proxies=self.proxy)
        print("请求{}，响应状态码:{}".format(me_url,resp.status_code)) 
        print(resp.text)
        # self.save_file('me',resp.text)

    def encrypt(self, string):

        with open('./zhihu.js', 'r', encoding='utf-8') as f:
            js = f.read()
        result = execjs.compile(js).call('encrypt', string)
        return result

    def get_signature(self):

        h = hmac.new(key='d1b964811afb40118a12068ff74a12f4'.encode('utf-8'), digestmod=sha1)
        grant_type = 'password'
        client_id = 'c3cef7c66a1843f8b3a9e6a1e3160e20'
        source = 'com.zhihu.web'
        now = self.time_str
        h.update((grant_type + client_id + source + now).encode('utf-8'))
        return h.hexdigest()

    def save_file(self, name, html):

        with open('{}.html'.format(name),'w',encoding='utf-8') as f:
            f.write(html)

    def verify_data(self, soup_data, url, headers=None):
        if not headers:
            headers = self.headers
        if not soup_data.find('script', {'id': 'js-initialData'}):
            time.sleep(15)
            print('重试获取数据！')
            res = self.session.get(url, headers=headers, proxies=self.proxy)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, "html.parser")
            if not soup.find('script', {'id': 'js-initialData'}):
                return False
            else:
                return soup
        else:
            return soup_data

    def get_followers(self, page):
        url = "https://www.zhihu.com/people/kaifulee/followers?page={0}".format(page)
        response = self.session.get(url, headers=self.headers, proxies=self.proxy)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text,"html.parser")
        soup_data = self.verify_data(soup, url)
        if soup_data:
            js_data = json.loads(soup.find('script', {'id': 'js-initialData'}).get_text())
            user_dict = js_data['initialState']['entities']['users']
            return user_dict
        else:
            return None

    def get_user_info(self, url):
        response = self.session.get(url, headers=self.headers, proxies=self.proxy)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")
        soup_data = self.verify_data(soup, url)
        if soup_data:
            js_data = json.loads(soup.find('script', {'id': 'js-initialData'}).get_text())
            username = url.split('/')[-2]
            user_info_dict = js_data['initialState']['entities']['users'][username]
            return user_info_dict, username
        else:
            return False, False

    def answer_detail_info(self, session, username, answer_num, uid):
        print('正在爬取'+str(username)+'的回答！')
        itertime = answer_num//20 + 1
        for i in range(itertime):
            print('当前是第{0}页'.format(i+1))
            if i%16==0 and i!=0:
                self.proxy = get_random_ip()
                print('同一用户同一ip爬取回答16页，已自动更换ip！')
            url = 'https://www.zhihu.com/api/v4/members/{0}/answers?include=data%5B*%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Cmark_infos%2Ccreated_time%2Cupdated_time%2Creview_info%2Cexcerpt%2Cis_labeled%2Clabel_info%2Crelationship.is_authorized%2Cvoting%2Cis_author%2Cis_thanked%2Cis_nothelp%2Cis_recognized%3Bdata%5B*%5D.author.badge%5B%3F(type%3Dbest_answerer)%5D.topics%3B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20data%5B*%5D.question.has_publishing_draft%2Crelationship&offset={1}&limit=20&sort_by=created'.format(str(username), 20*i)
            refer = 'https://www.zhihu.com/people/{0}/answers'.format(str(username))
            _h = {'referer': refer}
            headers = {**self.headers, **_h}
            response = self.session.get(url, headers=headers, proxies=self.proxy)
            response.encoding = response.apparent_encoding
            json_data = json.loads(response.text)
            data_list = json_data['data']
            time.sleep(random.uniform(1,10))
            _hh = {'upgrade-insecure-requests': '1'}
            _headers = {**headers, **_hh}
            for item in data_list:
                _id = item['id']
                _qid = item['question']['id']
                _url = 'https://www.zhihu.com/question/' + str(_qid) + '/answer/' + str(_id)
                print(_url)
                comment_num = item['comment_count']
                agree_num = item['voteup_count']
                try:
                    answer_page = self.session.get(_url, headers=_headers, proxies=self.proxy)
                except ConnectionError:
                    print("ProxyError被捕获,暂停30s后更换代理ip后重试")
                    time.sleep(30)
                    self.proxy = get_random_ip()
                    answer_page = self.session.get(_url, headers=_headers, proxies=self.proxy)
                    if answer_page:
                        print("ProxyError已被恢复!")
                answer_page.encoding = answer_page.apparent_encoding
                soup = BeautifulSoup(answer_page.text, "html.parser")
                for j in range(5):
                    soup_data = self.verify_data(soup, url, _headers)
                    if soup_data:
                        break
                soup_data = soup.find('script', {'id': 'js-initialData'})
                if soup_data:
                    answer = json.loads(soup_data.get_text())
                    # print(topic_list)
                    if str(_qid) in answer['initialState']['entities']['questions']:
                        answer_detail = answer['initialState']['entities']['questions'][str(_qid)]
                        answer_title = answer_detail['title']
                        topic_list = answer_detail['topics']
                        topics = ','.join([x['name'] for x in topic_list])
                        new_answer = AnswerDetail(user_id=uid, answer_title=answer_title, agree_num=agree_num,
                            comment_num=comment_num, category=topics)
                        MySQLServices.insert(session, new_answer)
                    else:
                        print('该问题已被删除！')
                        time.sleep(random.uniform(1,10))
                        continue
                else:
                    print('获取{0}的第{1}页回答失败!'.format(username, i+1))
                    continue
                time.sleep(random.uniform(1,10))
            if json_data['paging']['is_end'] == True:
                print('paging is end!')
                break
        print('{}的回答爬取完成！'.format(username))

    def ask_detail_info(self, session, username, ask_num, uid):
        print('正在爬取{}的提问！'.format(username))
        itertime = ask_num//20 + 1
        for i in range(itertime):
            print('当前是第{}页'.format(i+1))
            if i%16==0 and i!=0:
                self.proxy = get_random_ip()
                print('同一用户同一ip爬取提问16页，已自动更换ip！')
            url = 'https://www.zhihu.com/api/v4/members/{0}/questions?include=data%5B*%5D.created%2Canswer_count%2Cfollower_count%2Cauthor%2Cadmin_closed_comment&offset={1}&limit=20'.format(username, 20*i)
            refer = 'https://www.zhihu.com/people/{0}/asks'.format(str(username))
            _h = {'refer': refer}
            headers = {**self.headers, **_h}
            response = self.session.get(url, headers=headers, proxies=self.proxy)
            response.encoding = response.apparent_encoding
            json_data = json.loads(response.text)
            data_list = json_data['data']
            time.sleep(random.uniform(1,10))
            _hh = {'upgrade-insecure-requests': '1'}
            _headers = {**headers, **_hh}
            for item in data_list:
                _qid = item['id']
                _url = 'https://www.zhihu.com/question/' + str(_qid)
                print(_url)
                answer_num = item['answer_count']
                follower_num = item['follower_count']
                try:
                    ask_page = self.session.get(_url, headers=_headers, proxies=self.proxy)
                except ConnectionError:
                    print("ProxyError被捕获,暂停30s后更换代理ip后重试")
                    time.sleep(30)
                    self.proxy = get_random_ip()
                    ask_page = self.session.get(_url, headers=_headers, proxies=self.proxy)
                    if ask_page:
                        print("ProxyError已被恢复!")
                ask_page.encoding = ask_page.apparent_encoding
                soup = BeautifulSoup(ask_page.text, "html.parser")
                for j in range(5):
                    soup_data = self.verify_data(soup, url, _headers)
                    if soup_data:
                        break
                soup_data = soup.find('script', {'id': 'js-initialData'})
                if soup_data:
                    ask = json.loads(soup_data.get_text())
                    # print(topic_list)
                    if str(_qid) in ask['initialState']['entities']['questions']:
                        ask_detail = ask['initialState']['entities']['questions'][str(_qid)]
                        ask_title = ask_detail['title']
                        topic_list = ask_detail['topics']
                        topics = ','.join([x['name'] for x in topic_list])
                        new_ask = AskDetail(user_id=uid, ask_title=ask_title, answer_num=answer_num,
                            follower_num=follower_num, category=topics)
                        MySQLServices.insert(session, new_ask)
                    else:
                        print('该问题已被删除！')
                        time.sleep(random.uniform(1,10))
                        continue
                else:
                    print('获取{0}的第{1}页提问失败!'.format(username, i+1))
                    continue
                time.sleep(random.uniform(1,10))
            if json_data['paging']['is_end'] == True:
                print('paging is end!')
                break
        print('{}的提问爬取完成！'.format(username))

def insert_user_info(user_info_dict, user, uname, session):
    if not user_info_dict:
        print('获取{0}用户信息失败！'.format(user.url) )
        break
    if len(user_info_dict) < 10:
        print('{0}用户信息不存在,请检查该用户是否存在！'.format(uname))
        continue
    if len(user_info_dict['locations']) == 0:
        location = ''
    else:
        location = user_info_dict['locations'][0]['name']
    if 'name' in user_info_dict['business']:
        business = user_info_dict['business']['name']
    else:
        business = ''
    if len(user_info_dict['employments']) == 0:
        career = ''
        position = ''
    else:
        employment = user_info_dict['employments'][0]
        if 'company' in employment:
            career = employment['company']['name']
        else:
            career = ''
        if 'job' in employment:
            position = employment['job']['name']
        else:
            position = ''
    if len(user_info_dict['educations']) == 0:
        school = ''
        major = ''
    else:
        edu = user_info_dict['educations'][0]
        if 'school' in edu:
            school = edu['school']['name']
        else:
            school = ''
        if 'major' in edu:
            major = user_info_dict['educations'][0]['major']['name']
        else:
            major = ''

    new_user = UserInfos(username=user_info_dict['name'], answer_num=user_info_dict['answerCount'],
        ask_num=user_info_dict['questionCount'], location=location, business=business,
        career_exp=career, position=position, school=school, major=major,
        sex=user_info_dict['gender'])
    MySQLServices.insert(session, new_user)

if __name__ == "__main__":

    username = input("请输入账号：")
    password = input("请输入密码：")

    account = Zhihu(username, password)
    account.login()
    session = MySQLServices.ins()

    # for i in range(53404,1,-1):
    #     if i%500==0:
    #         account.proxy = get_random_ip()
    #         print("更换代理ip：" + account.proxy['http'])
    #     print('正在爬取第{0}页粉丝'.format(i))
    #     sleep = random.uniform(1,2)
    #     print('暂停{}秒'.format(sleep))
    #     time.sleep(sleep)
    #     user_dict = account.get_followers(i)
    #     bulk_users(user_dict, session)

    for i in range(10000):
        user = MySQLServices.get_one(session, UserInfo, id=i)
        if i%25==0:
            # _proxy = account.proxy['http']
            account.proxy = get_random_ip()
            print("更换代理ip为：" + account.proxy['http'])
            # proxy_list.remove(_proxy)
        if user.username == '李开复':
            continue
        else:
            url = 'https' + str(user.url)[4:] + '/answers'
            user_info_dict, uname = account.get_user_info(url)
            insert_user_info(user_info_dict, user, uname, session)
            time.sleep(random.uniform(10,40))
            account.answer_detail_info(session, uname, new_user.answer_num, new_user.id)
            time.sleep(10)
            account.ask_detail_info(session, uname, new_user.ask_num, new_user.id)









    

class Zhihu(object):

    def __init__(self, username, password):

        self.username = username
        self.password = password
        self.session = requests.session()
        self.headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36',
            'x-zse-83': '3_1.1'
        }
        self.proxy = get_random_ip()

    def login(self):

        # 请求login_url,udid_url,captcha_url加载所需要的cookie
        login_url = 'https://www.zhihu.com/signup?next=/'
        resp = self.session.get(login_url, headers=self.headers, proxies=self.proxy)        
        print("请求{}，响应状态码:{}".format(login_url,resp.status_code)) 

        udid_url = 'https://www.zhihu.com/udid'
        resp = self.session.post(udid_url, headers=self.headers, proxies=self.proxy)
        print("请求{}，响应状态码:{}".format(udid_url,resp.status_code)) 
        # print(self.session.cookies.get_dict())

        captcha_url = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=en'
        resp = self.session.get(captcha_url, headers=self.headers, proxies=self.proxy)
        print("请求{}，响应状态码:{}".format(captcha_url,resp.status_code)) 
        # print(self.session.cookies.get_dict())
        # print(resp.text)
        # self.save_file('captcha',resp.text)
        
        # 校验是否需要验证吗，需要则直接退出，还没遇到过需要验证码的
        if re.search('true',resp.text):
            print('需要验证码')
            exit()
        
        # 获取signature参数
        self.time_str = str(int(time.time()*1000))
        signature = self.get_signature()
        # print(signature)

        # 拼接需要加密的字符串
        string = "client_id=c3cef7c66a1843f8b3a9e6a1e3160e20&grant_type=password&timestamp={}&source=com.zhihu.web&signature={}&username={}&password={}&captcha=&lang=en&ref_source=homepage&utm_source=".format(self.time_str,signature,self.username,self.password)
        # print(string)
        # 加密字符串
        encrypt_string = self.encrypt(string)
        # print(encrypt_string)

        # post请求登陆接口
        post_url = "https://www.zhihu.com/api/v3/oauth/sign_in"
        resp = self.session.post(post_url, data=encrypt_string, headers=self.headers, proxies=self.proxy)
        print("请求{}，响应状态码:{}".format(post_url,resp.status_code)) 
        # print(self.session.cookies.get_dict())
        # print(resp.text)
        # self.save_file('post',resp.text)

        # 校验是否登陆成功
        if re.search('user_id',resp.text):
            print('登陆成功')
        else:
            print("登陆失败")
            exit()

    def test(self):

        # 请求个人信息接口查看个人信息
        me_url = 'https://www.zhihu.com/api/v4/me'
        data = {
            'include': 'ad_type;available_message_types,default_notifications_count,follow_notifications_count,vote_thank_notifications_count,messages_count;draft_count;following_question_count;account_status,is_bind_phone,is_force_renamed,email,renamed_fullname;ad_type'
        }
        resp = self.session.get(me_url, data=data, headers=self.headers, proxies=self.proxy)
        print("请求{}，响应状态码:{}".format(me_url,resp.status_code)) 
        print(resp.text)
        # self.save_file('me',resp.text)

    def encrypt(self, string):

        with open('./zhihu.js', 'r', encoding='utf-8') as f:
            js = f.read()
        result = execjs.compile(js).call('encrypt', string)
        return result

    def get_signature(self):

        h = hmac.new(key='d1b964811afb40118a12068ff74a12f4'.encode('utf-8'), digestmod=sha1)
        grant_type = 'password'
        client_id = 'c3cef7c66a1843f8b3a9e6a1e3160e20'
        source = 'com.zhihu.web'
        now = self.time_str
        h.update((grant_type + client_id + source + now).encode('utf-8'))
        return h.hexdigest()

    def save_file(self, name, html):

        with open('{}.html'.format(name),'w',encoding='utf-8') as f:
            f.write(html)

    def get_followers(self, page):
        url = "https://www.zhihu.com/people/kaifulee/followers?page={0}".format(page)
        response = self.session.get(url, headers=self.headers, proxies=self.proxy)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text,"html.parser")
        js_data = json.loads(soup.find('script', {'id': 'js-initialData'}).get_text())
        user_dict = js_data['initialState']['entities']['users']
        return user_dict


if __name__ == "__main__":

    account = Zhihu('15253183997','g6h53z601')
    account.login()
    # account.test()
    session = MySQLServices.ins()
    print("当前使用ip：" + account.proxy['http'])
    for i in range(53475,1,-1):
        if i%500==0:
            account.proxy = get_random_ip()
            print("更换代理ip：" + account.proxy['http'])
        print('正在爬取第{0}页粉丝'.format(i))
        sleep = random.uniform(1,2)
        print('暂停{}秒'.format(sleep))
        time.sleep(sleep)
        user_dict = account.get_followers(i)
        bulk_users(user_dict, session)
        session.commit()




