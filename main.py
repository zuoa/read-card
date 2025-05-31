import datetime
import io
import json
import os

from dotenv import load_dotenv
from flask import Flask, request, render_template, jsonify, redirect, url_for
from playhouse.shortcuts import model_to_dict

from utils import llm_chat

app = Flask(__name__, static_folder='static')

# Load environment variables
load_dotenv()


@app.route('/', methods=['GET'])
def index_page():
    # GET request: display the form with default values
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5020)
