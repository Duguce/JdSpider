# -*- coding: utf-8  -*-
# @Author  : Yu Ching San 
# @Email   : zhgyqc@163.com
# @Time    : 2023/8/10 11:53
# @File    : config.py
# @Software: PyCharm
import os

# Data path for storing product reviews and Q&A data
DATA_PATH = os.path.join(os.getcwd(), 'output')

# Maximum number of worker threads
MAX_WORKERS = 3

# Product ID
PRODUCT_ID = 100015394631

# Comment parameters
COMMENT_PARAM = {
    'pages': 50,      # Number of pages to crawl (Jingdong limits to a maximum of 50 pages)
    'score': 1,        # Comment type (0: All, 3: Positive, 2: Neutral, 1: Negative)
    'sort_type': 6,    # Comment sorting method (5: Recommended sorting, 6: Time sorting)
    'page_size': 10,   # Number of comments to display per page
}

QA_PARAM = {
    'pages': 50,  # Number of pages to crawl (Jingdong limits to a maximum of 50 pages)
}

# Username and password for logging in to Jingdong
USERNAME = ''
PASSWORD = ''

# Path to store the product ID
PRODUCT_ID_DIR = "./ids_collection"

# Keywords to search for
KEYWORDS_TO_SEARCH = [
    '千禧年钻戒', '施华洛世奇项链', '黄金手链',
]