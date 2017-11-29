#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import Queue
import settings
import six.moves
import threading

from six.moves.urllib.request import build_opener, HTTPCookieProcessor, Request, install_opener, urlopen
from six.moves.urllib.parse import urlencode


BASE_URL = 'https://courses.edx.org'
EDX_HOMEPAGE = BASE_URL + '/login'
LOGIN_API = BASE_URL + '/user_api/v1/account/login_session/'

TEMPLAGE_DISCUSS_INDEX_URL = 'https://courses.edx.org/courses/course-v1:{}/discussion/forum?ajax=1&page={}&sort_key=date&sort_order=desc'
TEMPLAGE_THREAD_URL = 'https://courses.edx.org/courses/course-v1:{}/discussion/forum/i4x-TsinghuaX-30240184x-course-1T2014/threads/{}?ajax=1'

headers = {
    'Accept': '*/*',
    'Referer': EDX_HOMEPAGE,
    'X-Requested-With': 'XMLHttpRequest',
}

jar = six.moves.http_cookiejar.CookieJar()
opener = build_opener(HTTPCookieProcessor(jar))
install_opener(opener)
opener.open(EDX_HOMEPAGE)

def get_initial_token():
    for cookie in jar:
        if cookie.name == 'csrftoken':
            return cookie.value
    return ''

DEFAULT_USER_AGENTS = {"google-chrome": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.63 Safari/537.31",
                       "firefox": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:24.0) Gecko/20100101 Firefox/24.0",
                       "default": 'edX-downloader/0.01'}
USER_AGENT = DEFAULT_USER_AGENTS["default"]
headers = {
    'User-Agent': USER_AGENT,
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Referer': EDX_HOMEPAGE,
    'X-Requested-With': 'XMLHttpRequest',
    'X-CSRFToken': get_initial_token(),
}

def jsonapi(url, data=None):
    response = urlopen(Request(url, data, headers))
    return json.loads(response.read())

response = urlopen(Request(LOGIN_API, urlencode({'email': settings.USER_EMAIL('edx'), 'password': settings.USER_PSWD('edx'), 'remember': False}).encode('utf-8'), headers))

n_threads = 16

p = Queue.Queue()
q = Queue.Queue()

discuss_index = {k: None for k in settings.COURSES_EDX}

for k, v in settings.COURSES_EDX.items():
    p.put((k, 0))

def parallel_work_0(tid):
    while True:
        try:
            args = p.get(block=False)
            print(args)
        except Queue.Empty as e:
            return
        courseid, page = args
        res = jsonapi(TEMPLAGE_DISCUSS_INDEX_URL.format(courseid, page + 1))
        num_pages = res['num_pages']
        discuss_index[courseid] = [res]
        for i in range(1, num_pages):
            q.put((courseid, i))
            discuss_index[courseid].append(None)

def parallel_work_1(tid):
    while True:
        try:
            args = q.get(block=False)
            print(args)
        except Queue.Empty as e:
            return
        courseid, page = args
        res = jsonapi(TEMPLAGE_DISCUSS_INDEX_URL.format(courseid, page + 1))
        discuss_index[courseid][page] = res
threads = [threading.Thread(target=parallel_work_0, args=(i, )) for i in range(n_threads)]
for t in threads:
    t.start()
for t in threads:
    t.join()

threads = [threading.Thread(target=parallel_work_1, args=(i, )) for i in range(n_threads)]
for t in threads:
    t.start()
for t in threads:
    t.join()

q = Queue.Queue()
posts = {}
for courseid in discuss_index:
    ps = {}
    for page in discuss_index[courseid]:
        for dis in page['discussion_data']:
            postid = dis['id']
            q.put((courseid, postid))
            ps[postid] = None
    posts[courseid] = ps

def parallel_work_2(tid):
    while True:
        try:
            args = q.get(block=False)
            print(args)
        except Queue.Empty as e:
            return
        courseid, postid = args
        try:
            res = jsonapi(TEMPLAGE_THREAD_URL.format(courseid, postid))
        except ValueError as e:
            res = None
        posts[courseid][postid] = res

threads = [threading.Thread(target=parallel_work_2, args=(i, )) for i in range(n_threads)]
for t in threads:
    t.start()
for t in threads:
    t.join()
for courseid in posts:
    posts[courseid] = dict(filter(lambda t: t[1] is not None, posts[courseid].items()))

output = []
for courseid, pt in posts.items():
    output.append({
        'platform': 'edx',
        'course_id': courseid,
        'course_name': settings.COURSES_EDX[courseid],
        'posts': pt
        })
with open('db_edx.js', 'w') as f:
    f.write('/**/var db_edx = ')
    json.dump(output, f)
    f.write(';')
