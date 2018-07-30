# -*- coding: UTF-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
import six


rep_struct = [{
    'created_at': six.text_type,
    'body': six.text_type,
    'children': [{
        'created_at': six.text_type,
        'body': six.text_type,
    }],
},]

post_struct = {
    'content': {
        'id': six.text_type,
        'created_at': six.text_type,
        'title': six.text_type,
        'body': six.text_type,
        'commentable_id': six.text_type,
        'comments_count': int,
        'children': rep_struct,
        'endorsed_responses': rep_struct,
        'non_endorsed_responses': rep_struct,
    }
}


def cleanup(d, target):
    if isinstance(target, type):
        assert isinstance(d, target), (type(d), target)
    else:
        assert type(d) is type(target)
        if isinstance(target, dict):
            for key in list(d.keys()):
                if key in target:
                    cleanup(d[key], target[key])
                else:
                    del d[key]
        elif isinstance(target, list):
            for v in d:
                cleanup(v, target[0])
    return d


def cleanup_post(post):
    return cleanup(post, post_struct)


# just a test
if __name__ == '__main__':
    with open('db_edx.js') as f:
        s = f.read()
    s = s[s.index('=') + 1:s.rindex(';')]
    db = json.loads(s)
    for course in db:
        for post_id, post in course['posts'].items():
            cleanup_post(post)
    print('pass')
