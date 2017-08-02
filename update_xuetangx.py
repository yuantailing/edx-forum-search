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


BASE_URL = 'https://www.xuetangx.com'
EDX_HOMEPAGE = BASE_URL + '/v2/login_ajax'
LOGIN_API = BASE_URL + '/v2/login_ajax'

TEMPLAGE_DISCUSS_INDEX_URL = 'http://www.xuetangx.com/courses/course-v1:{}/discussion/forum?ajax=1&page={}&sort_key=date&sort_order=desc'
TEMPLAGE_THREAD_URL = 'http://www.xuetangx.com/courses/course-v1:{}/discussion/forum/i4x-edx-templates-course-Empty/threads/{}?ajax=1'

headers = {
    'Accept': '*/*',
    'Referer': EDX_HOMEPAGE,
    'X-Requested-With': 'XMLHttpRequest',
}

jar = six.moves.http_cookiejar.CookieJar()
opener = build_opener(HTTPCookieProcessor(jar))
install_opener(opener)
opener.open(EDX_HOMEPAGE)

def jsonapi(url, data=None):
    response = urlopen(Request(url, data, headers))
    return json.loads(response.read())

res = jsonapi(LOGIN_API, urlencode({'username': settings.USER_EMAIL('xuetangx'), 'password': settings.USER_PSWD('xuetangx'), 'remember': False}).encode('utf-8'))
assert res['success'] is True

n_threads = 64

p = Queue.Queue()
q = Queue.Queue()

discuss_index = {k: None for k in settings.COURSES_XUETANGX}

for k, v in settings.COURSES_XUETANGX.items():
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
        res = jsonapi(TEMPLAGE_THREAD_URL.format(courseid, postid))
        posts[courseid][postid] = res

threads = [threading.Thread(target=parallel_work_2, args=(i, )) for i in range(n_threads)]
for t in threads:
    t.start()
for t in threads:
    t.join()

output = []
for courseid, pt in posts.items():
    output.append({
        'platform': 'xuetangx',
        'course_id': courseid,
        'course_name': settings.COURSES_XUETANGX[courseid],
        'posts': pt
        })
with open('db_xuetangx.js', 'w') as f:
    f.write('/**/var db_xuetangx = ')
    json.dump(output, f)
    f.write(';')
