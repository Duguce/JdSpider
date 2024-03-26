# -*- coding: utf-8  -*-
# @Author  : Yu Ching San
# @Email   : zhgyqc@163.com
# @Time    : 2023/8/10 11:50
# @File    : comment_spider.py
# @Software: PyCharm
import concurrent.futures
import json
import random
import threading
import time

import pandas as pd
import requests
from fake_useragent import UserAgent
from loguru import logger

from config import COMMENT_PARAM, DATA_PATH, MAX_WORKERS, PRODUCT_ID


class JDCommentSpider:
    """Class for scraping product comments from https://www.jd.com.

    Args:
        comment_param (dict): Dictionary containing parameters for comments.
        product_id (str): ID of the product to fetch comments for.
        data_path (str): Path to store the scraped data.
        max_workers (int): Maximum number of concurrent threads.

    Attributes:
        comm_data (pd.DataFrame): DataFrame to store the scraped comments.
        comm_data_lock (threading.Lock): Thread lock for data synchronization.
        max_workers (int): Maximum number of concurrent threads.
        product_id (str): ID of the product.
        pages (int): Number of pages to scrape.
        score (int): Desired comment score filter.
        sort_type (int): Sorting type for comments.
        page_size (int): Number of comments per page.
        data_path (str): Path to store the scraped data.
    """

    def __init__(self, comment_param=COMMENT_PARAM, product_id=None, data_path=DATA_PATH, max_workers=MAX_WORKERS):
        self.comm_data = []  # list to store Q&A data
        self.comm_data_lock = threading.Lock()  # Thread lock
        self.max_workers = max_workers  # Maximum number of threads
        self.product_id = None  # Product ID (initialize as None)
        self.pages = comment_param['pages']  # Number of pages to scrape
        self.score = comment_param['score']  # Comment score filter
        # Sorting type for comments
        self.sort_type = comment_param['sort_type']
        # Number of comments per page
        self.page_size = comment_param['page_size']
        self.data_path = data_path  # Data storage path

    def send_request(self, url):
        """Send a request to the specified URL.

        Args:
            url (str): The URL to send the request to.

        Returns:
            str: The response text.
        """
        headers = {'user-agent': UserAgent().random}  # Generate random user agent
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Check if the request was successful
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed, error message: {e}...")
            raise

    def get_comments(self, page):
        """Get product comments for the specified page.

        Args:
            page (int): The page number.

        Returns:
            str: The response text.
        """
        api_url = f'https://api.m.jd.com/?appid=item-v3&functionId=pc_club_productPageComments&' \
                  f'productId={self.product_id}&score={self.score}&sortType={self.sort_type}&page={page}&pageSize={self.page_size}&isShadowSku=0&fold=0&bbtf=&shield'
        response_data = self.send_request(api_url)
        logger.info(
            f"Fetching comments for product ID {self.product_id}, page {page + 1}...")
        return response_data

    def parse_comments(self, response):
        """Parse product comments from the response.

        Args:
            response (str): The response text.

        Returns:
            pd.DataFrame: DataFrame containing parsed comments.
        """
        json_obj = json.loads(response)
        comments = json_obj.get('comments', [])
        comm_list = []  # List to store comments
        for comment in comments:
            user_id = comment.get('id', '')
            user_name = comment.get('nickname', '')
            content = comment.get('content', '').replace('\n', ' ')  # replace newline characters with spaces
            create_time = comment.get('creationTime', '')
            score = comment.get('score', '')
            location = comment.get('location', '')
            product_name = comment.get('referenceName', '')
            comm_list.append([user_id, user_name, content, create_time,
                             score, location, self.product_id, product_name])

        temp_df = pd.DataFrame(comm_list,
                               columns=['user_id', 'user_name', 'content', 'create_time', 'score', 'location',
                                        'product_id',
                                        'product_name'])  # Generate temporary DataFrame

        return temp_df

    def save_comments(self, comm_data):
        """Save product comments to an Excel file.

        Args:
            comm_data (pd.DataFrame): DataFrame containing product comments.

        Returns:
            None
        """
        if len(comm_data) <= 1:  # Check if there's only the header row
            logger.warning("No data to save. Skipping CSV file creation...")
            return

        try:
            comm_data.to_csv(f"{self.data_path}/com_{self.product_id}.csv", index=False)
            logger.info(
                f"Saved comments for product ID {self.product_id} to file...")
        except Exception as e:
            logger.error(
                f"Failed to save comments for product ID {self.product_id} to file, error message: {e}...")

    def crawl_page(self, page):
        """Crawl comments for a specific page.

        Args:
            page (int): The page number.

        Returns:
            None
        """
        # response = self.get_comments(page)
        # comments = self.parse_comments(response)
        # with self.comm_data_lock:
        #     self.comm_data = pd.concat(
        #         [self.comm_data, comments], ignore_index=True)

        # time.sleep(random.uniform(1, 3))
        response = self.get_comments(page)
        if not response:
            logger.warning(f"No response received for page {page}. Skipping...")
            return
        comments = self.parse_comments(response)
        if comments.empty:
            logger.warning(f"No comments data found for page {page}. Skipping...")
            return
        with self.comm_data_lock:
            self.comm_data = pd.concat(
                [self.comm_data, comments], ignore_index=True)

        time.sleep(random.uniform(3, 5))

    def start_crawling(self, product_id):
        """Start crawling product comments.

        Args:
            product_id (str): ID of the product to fetch comments for.

        Returns:
            None
        """
        # Update the product_id attribute
        self.product_id = product_id
        
        logger.info(f"Fetching comments for product ID {self.product_id}...")
        
        # Clear comments data
        self.comm_data = pd.DataFrame(
                    columns=['user_id', 'user_name', 'content', 'create_time', 'score', 'location', 'product_id',
                            'product_name'])

        # Create a thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for page in range(self.pages):  # Fetch pages
                executor.submit(self.crawl_page, page)

        logger.info(
            f"Completed fetching comments for product ID {self.product_id}...")
        self.save_comments(self.comm_data)  # Save data
