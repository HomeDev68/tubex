# TubeX
A forward proxy to YouTube written in Python using Flask, requests, and pytube.

## Introduction
By deploying this tiny forward proxy on your VPS as a website, you can:
* search and watch YouTube videos without reverse proxy;
* watch YouTube videos online without ads;
* watch YouTube videos with accelerated play rates;
* watch/download YouTube videos in different qualities (360p/720p).

## Usage
Install TubeX by pip:
* pip install flask requests pytube
* cd ~/tubex

Put your app.key and app.crt in this folder, or create a self-signed certificate with openssl:
* openssl req -x509 -sha256 -nodes -days 3650 -newkey rsa:2048 -keyout app.key -out app.crt

Then start the server in the background:
* sudo nohup python3 server.py >> tubex.log 2>&1 &

Now you can access your website in browsers.

## Screenshots
### Search results
![image](https://github.com/dreamrover/screenshots/blob/master/TED.png)
### Watch online
![image](https://github.com/dreamrover/screenshots/blob/master/Shara.png)
