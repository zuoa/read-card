import datetime
import io
import json
import os

from dotenv import load_dotenv
from flask import Flask, request, render_template, jsonify, redirect, url_for, send_file
from playhouse.shortcuts import model_to_dict

from utils import llm_chat, get_markdown_from_url, extract_core_sentences_from_markdown, draw_sentences_image

app = Flask(__name__, static_folder='static')

# Load environment variables
load_dotenv()

# 添加请求日志中间件
@app.before_request
def log_request_info():
    print('Headers:', dict(request.headers))
    print('URL:', request.url)
    print('Method:', request.method)

@app.route('/', methods=['GET'])
def index_page():
    # GET request: display the form with default values
    return render_template('index.html')



@app.route('/view/<path:ori_url>', methods=['GET'])
def view_core_segments(ori_url):
    if not ori_url:
        return jsonify({'error': '缺少 url 参数'}), 400
    markdown = get_markdown_from_url(ori_url)
    if not markdown:
        print(f"Failed to get markdown for URL: {ori_url}")  # 添加日志
        return jsonify({'error': '获取原文失败'}), 500
    quotes = extract_core_sentences_from_markdown(markdown)
    if not quotes:
        print(f"Failed to extract sentences from markdown for URL: {ori_url}")  # 添加日志
        return jsonify({'error': '提炼核心语句失败'}), 500
    print(f"Extracted sentences: {quotes}")  # 添加日志
    return render_template('card.html', quotes=quotes, ori_url=ori_url, day=datetime.datetime.now().strftime("%Y/%m/%d"), title='READ CARD ' + datetime.datetime.now().strftime("%Y/%m/%d"))

@app.route('/render/<path:ori_url>', methods=['GET'])
def core_sentences_image(ori_url):
    print(f"Received request for URL: {ori_url}")  # 添加日志
    if not ori_url:
        print("URL is empty")  # 添加日志
        return jsonify({'error': '缺少 url 参数'}), 400
    markdown = get_markdown_from_url(ori_url)
    if not markdown:
        print(f"Failed to get markdown for URL: {ori_url}")  # 添加日志
        return jsonify({'error': '获取原文失败'}), 500
    quotes = extract_core_sentences_from_markdown(markdown)
    if not quotes:
        print(f"Failed to extract sentences from markdown for URL: {ori_url}")  # 添加日志
        return jsonify({'error': '提炼核心语句失败'}), 500
    img_io = draw_sentences_image(quotes)
    return send_file(img_io, mimetype='image/png')


if __name__ == '__main__':
    print("Registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.rule}")
    app.run(debug=True, host='0.0.0.0', port=5030)
