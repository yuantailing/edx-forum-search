# edx-forum-search

EDX / XUETANGX 讨论区离线搜索

先登录帐号，把讨论区数据下载到本地。然后打开 `index.html` 使用搜索功能。

  * 可选择搜索范围，支持标题、正文、回复、二级回复
  * 可选择搜索课程
  * 搜索结果按时间从近到远排序
  * 支持多关键词，用空格分隔
  * 搜索结果中的关键词高亮显示
  * 搜索结果提供跳转链接，可跳转到 EDX / XUETANGX 讨论区


## Usage

```
$ pip install -r requirements.txt
$ cp settings.py.sample settings.py
$ python update_edx.py
$ python update_xuetangx.py
```

Then, you can browse `index.html`.

注：请确保输入的帐号有权限访问 `settings.py` 里的课程。
