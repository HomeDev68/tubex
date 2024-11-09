from flask import Flask, request, redirect, send_file
from yt_dlp import YoutubeDL
import requests
import zlib
import base64
import json
from io import BytesIO

app = Flask(__name__)

favicon = "https://img.icons8.com/color/48/000000/rotube.png"

def create_head(title):
    return f"""
    <head>
        <title>TubeX{' - ' + title if title else ''}</title>
        <link rel="shortcut icon" href={favicon} type="image/x-icon" />
        <style>
            table, th, td {{
                font-family: arial, sans-serif;
                border: 1px solid #cccccc;
                border-collapse: collapse;
            }}
            th {{
                padding: 5px;
                text-align: center;
            }}
            td {{
                padding: 5px;
                text-align:left;
            }}
        </style>
    </head>
    """

def create_table(arr, caption):
    if not arr or not len(arr):
        return ''
    first = ''.join([f'<th>{e}</th>' for e in arr[0].keys()])
    rows = [f'<tr>{first}</tr>']
    for r in arr:
        line = ''.join([f'<td>{e or ""}</td>' for e in r.values()])
        rows.append(f'<tr>{line}</tr>')
    return f"""
    <table style="word-wrap:break-word">
        {f'<caption><h4>{caption}</h4></caption>' if caption else ''}
        {'\n        '.join(rows)}
    </table><br>
    """

def create_page(title, keyword, extra):
    return f"""
    <html>
        {create_head(title)}
        <h1 style="text-align:center;">TubeX</h1>
        <body>
            <form action="/result" method="get" style="text-align:center;">
                <p><input type="text" size=30 name="search_query" value="{keyword or ''}"><input type="submit" value="Go"></p>
                <p><input type="radio" id="radio1" name="t" value="kw" checked><label for="radio1">keyword</label>
                <input type="radio" id="radio2" name="t" value="id"><label for="radio2">url/id</label></p>
            </form>
            {extra or ''}
        </body>
    </html>
    """

def create_result_content(result):
    arr = [{
        'thumbnail': f'<img width="180" height="101" src="{e["thumbnail"]}" />',
        'detail': f'<p><a href="./watch?v={e["id"]}"><h4>{e["title"]}</h4></a></p><p>{e["type"]}&emsp;<b>{sec_to_str(e["duration"])}</b>&emsp;{e["views"]} views&emsp;{e["uploadedAt"]}&emsp;@<b>{e["author"]}</b></p><p>{e["description"] or ""}</p>'
    } for e in result['items']]
    return f"""
    <center>
        <h3>{result['original']}:</h3>
        <p>{result['results']} results</p>
        {create_table(arr, 'Search Results')}
    </center>
    """

def create_video_source(video):
    if not video or not video['formats'] or not len(video['formats']):
        return ''
    arr = [f'<source src="./{encode_url(e["url"])}/{video["title"].replace("/", "")}.{e["container"]}" type="{e["mimeType"]}" label="{e["qualityLabel"]}"{" selected=\"true\"" if i == 0 else ""}>' for i, e in enumerate(video['formats'])]
    return '\n'.join(arr)

def create_watch_content(video):
    downloads = [{
        'format': e['container'],
        'quality': e['qualityLabel'],
        'size': f'{int(e["contentLength"]):,}' if e['contentLength'] else 'unknown',
        'get': f'<a href="./{encode_url(e["url"])}/{video["title"].replace("/", "")}.{e["container"]}" download>download</a>',
        'url': f'<input name="url" readonly="readonly" value="{e["url"]}">'
    } for e in video['formats']]
    relates = [{
        'thumbnail': f'<img width="168" height="94" src="{e["thumbnail"]}" />',
        'detail': f'<a href="./watch?v={e["id"]}"><h4>{e["title"]}</h4></a><p><b>{sec_to_str(e["duration"])}</b>&emsp;{e["views"]} views&emsp;{e["published"]}&emsp;@<b>{e["author"]}</b></p>'
    } for e in video['related']]
    return f"""
    <style>
        .video-js {{
            width: {video['formats'][0]['width']}px;
            height: {video['formats'][0]['height']}px;
        }}
    </style>
    <link href="https://vjs.zencdn.net/7.11.4/video-js.css" rel="stylesheet">
    <link href="https://unpkg.com/@silvermine/videojs-quality-selector/dist/css/quality-selector.css" rel="stylesheet">
    <link href="https://7ds7.github.io/videojs-vjsdownload/dist/videojs-vjsdownload.css" rel="stylesheet">
    <center>
        <video id="videojs-player" class="video-js" controls preload="auto" width="{video['formats'][0]['width']}" height="{video['formats'][0]['height']}" poster="{video['poster']}">
            {create_video_source(video)}
        </video>
        <p><h4>{video['title']}</h4></p>
        <p><b>{sec_to_str(video['duration'])}</b>&emsp;{video['views']:,} views&emsp;{video['date']}&emsp;@<b>{video['author']}</b></p>
        <p align="left" style="width:{video['formats'][0]['width']-20}px"><font size="-1">{video['description'].replace('\n', '<br>') if video['description'] else ''}</font></p>
        {create_table(downloads)}
        {create_table(relates, 'related videos')}
    </center>
    <script src="https://vjs.zencdn.net/7.11.4/video.min.js"></script>
    <script src="https://videojs.github.io/videojs-playbackrate-adjuster/dist/browser/videojs-playbackrate-adjuster.js"></script>
    <script src="https://unpkg.com/@silvermine/videojs-quality-selector/dist/js/silvermine-videojs-quality-selector.min.js"></script>
    <script src="https://7ds7.github.io/videojs-vjsdownload/dist/videojs-vjsdownload.js"></script>
    <script>
        var player = videojs('videojs-player', {{playbackRates: [1, 1.25, 1.5, 2]}});
        player.controlBar.addChild('qualitySelector');
        player.vjsdownload();
    </script>
    """

def encode_url(url):
    return base64.urlsafe_b64encode(zlib.compress(url.encode())).decode()

def decode_url(str):
    return zlib.decompress(base64.urlsafe_b64decode(str.encode())).decode()

def sec_to_str(sec):
    sec = float(sec)
    if sec < 10:
        return f'0:0{int(sec)}'
    if sec < 60:
        return f'0:{int(sec)}'
    if sec < 3600:
        return f'{int(sec // 60)}:{int(sec % 60):02d}'
    return f'{int(sec // 3600)}:{int(sec % 3600 // 60):02d}:{int(sec % 60):02d}'

@app.route('/')
def index():
    return create_page('', '', '')

@app.route('/result')
def result():
    keyword = request.args.get('search_query')
    if not keyword:
        return redirect('/')
    t = request.args.get('t')
    if t == 'id':
        return redirect(f'/watch?v={keyword}')
    ydl_opts = {
        'format': 'best',
        'noplaylist': True,
        'quiet': True,
        'extract_flat': True
    }
    with YoutubeDL(ydl_opts) as ydl:
        res = ydl.extract_info(f"ytsearch:{keyword}", download=False)['entries']
    result = {
        'original': keyword,
        'results': len(res),
        'items': [{
            'thumbnail': f'./thumbnail?url={encode_url(e.get("thumbnail", ""))}&encoded=1' if e.get("thumbnail") else '',
            'id': e.get('id', ''),
            'title': e.get('title', ''),
            'type': 'video',
            'duration': e.get('duration', 0),
            'views': e.get('view_count', 0),
            'uploadedAt': e.get('upload_date', ''),
            'author': e.get('uploader', ''),
            'description': e.get('description', '')
        } for e in res if e.get('duration', 0)]
    }
    return create_page(keyword, keyword, create_result_content(result))

@app.route('/watch')
def watch():
    id = request.args.get('v')
    if not id:
        return redirect('/')
    ydl_opts = {
        'format': 'best',
        'noplaylist': True,
        'quiet': True
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f'https://www.youtube.com/watch?v={id}', download=False)
    video = {
        'title': info['title'],
        'poster': f'./thumbnail?url={info["thumbnail"]}',
        'duration': info['duration'],
        'views': info['view_count'],
        'date': info['upload_date'],
        'author': info['uploader'],
        'description': info['description'],
        'formats': [{
            'url': f'https://www.youtube.com/watch?v={id}',
            'container': f'{info["ext"]}',
            'mimeType': f'video/{info["ext"]}',
            'qualityLabel': f'{info["height"]}p',
            'contentLength': f'{info["filesize"]}',
            'width': f'{info["width"]}',
            'height': f'{info["height"]}'
        }],
        'related': [{
            'thumbnail': f'./thumbnail?url={encode_url(e["thumbnail"])}&encoded=1',
            'id': e['id'],
            'title': e['title'],
            'duration': e['duration'],
            'views': e['view_count'],
            'published': e['upload_date'],
            'author': e['uploader']
        } for e in info['related']]
    }
    return create_page(video['title'], None, create_watch_content(video))

@app.route('/thumbnail')
def thumbnail():
    url = decode_url(request.args.get('url')) if request.args.get('encoded') else request.args.get('url')
    res = requests.get(url, stream=True)
    return send_file(BytesIO(res.content), mimetype=res.headers['Content-Type'])

@app.route('/<path:url>/<name>')
def download(url, name):
    url = decode_url(url)
    headers = {'Range': request.headers.get('Range')} if request.headers.get('Range') else {}
    res = requests.get(url, headers=headers, stream=True)
    return send_file(BytesIO(res.content), mimetype=res.headers['Content-Type'], as_attachment=True, attachment_filename=name)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
# app.run(host='0.0.0.0', port=8000, ssl_context=('app.crt', 'app.key'))
