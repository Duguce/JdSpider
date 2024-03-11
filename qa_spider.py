# -*- coding: utf-8  -*-
# @Author  : Yu Ching San
# @Email   : zhgyqc@163.com
# @Time    : 2023/8/21 10:46
# @File    : qa_spider.py
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

from config import DATA_PATH, MAX_WORKERS, PRODUCT_ID, QA_PARAM


class JDQASpider:
    """Class for scraping product question and answer (Q&A) data from https://www.jd.com.

    Args:
        qa_param (dict): Dictionary containing parameters for Q&A.
        product_id (str): ID of the product to fetch Q&A for.
        data_path (str): Path to store the scraped data.
        max_workers (int): Maximum number of concurrent threads.

    Attributes:
        pages (int): Number of pages to scrape for Q&A.
        product_id (str): ID of the product.
        qa_data (pd.DataFrame): DataFrame to store the scraped Q&A data.
        qa_data_lock (threading.Lock): Thread lock for data synchronization.
        data_path (str): Path to store the scraped data.
        max_workers (int): Maximum number of concurrent threads.
    """

    def __init__(self, qa_param=QA_PARAM, product_id=None, data_path=DATA_PATH, max_workers=MAX_WORKERS):
        """Initialize the JDQASpider instance.

        Args:
            qa_param (dict): Dictionary containing parameters for Q&A.
            product_id (str): ID of the product to fetch Q&A for.
            data_path (str): Path to store the scraped data.
            max_workers (int): Maximum number of concurrent threads.
        """
        self.pages = qa_param['pages']  # Number of pages to scrape for Q&A
        self.product_id = None  # Product ID (initialize as None)
        self.qa_data = []  # list to store Q&A data
        self.qa_data_lock = threading.Lock()  # Thread lock
        self.data_path = data_path  # Data storage path
        self.max_workers = max_workers  # Maximum number of threads

    def send_request(self, url):
        """Send a request to the specified URL.

        Args:
            url (str): The URL to send the request to.

        Returns:
            str: The response text.
        """
        headers = {'user-agent': UserAgent().random}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed. Error: {e}...")

    def get_qa(self, page):
        """Get product question and answer (Q&A) data for a specific page.

        Args:
            page (int): The page number.

        Returns:
            str: The response data.
        """
        api_url = f'https://api.m.jd.com/?appid=item-v3&' \
                  f'functionId=getQuestionAnswerList&client=pc&clientVersion=1.0.0&page={page}&productId={self.product_id}'
        response_data = self.send_request(api_url)
        logger.info(
            f"Fetching Q&A data for product ID {self.product_id}, page {page}...")
        return response_data

    def get_answer(self, question_id):
        """Get answer data for a specific answer.

        Args:
            question_id (int): The question ID.

        Returns:
            str: The response data.
        """
        api_url = f'https://api.m.jd.com/?appid=item-v3&functionId=getAnswerListById&client=pc&clientVersion=1.0.0&page=1&questionId={question_id}'
        response_data = self.send_request(api_url)
        return response_data

    def parse_qa(self, response):
        """Parse product question and answer (Q&A) data from the response.

        Args:
            response (str): The response text.

        Returns:
            pd.DataFrame: The parsed Q&A data as a DataFrame.
        """
        json_obj = json.loads(response)
        qa_data = json_obj.get('questionList', [])
        qa_list = []
        try:
            for qa in qa_data:  # Iterate through each question
                id = qa.get('id', '')  # Question ID
                content = qa.get('content', '')  # Question content
                product_id = qa.get('productId', '')  # Product ID
                created_time = qa.get('created', '')  # Question creation time
                for answer in qa['answerList']:
                    answer_id = answer.get('id', '')
                    answer_content = answer.get('content', '')
                    answer_created_time = answer.get('created', '')
                    location = answer.get('location', '')
                    qa_list.append(
                        [id, content, product_id, created_time, answer_id, answer_content, answer_created_time,
                         location])
        except Exception as e:
            print(e)
        qa_df = pd.DataFrame(qa_list,
                             columns=['id', 'question_content', 'product_id', 'created_time', 'answer_id',
                                      'answer_content', 'answer_created_time', 'location'])

        return qa_df

    def save_data(self, qa_data):
        """Save product question and answer (Q&A) data to a CSV file.

        Args:
            qa_data (pd.DataFrame): The Q&A data to be saved.

        Returns:
            None
        """
        if len(qa_data) <= 1:  # Check if there's only the header row
            logger.warning("No data to save. Skipping CSV file creation...")
            return

        try:
            qa_data.to_csv(f"{self.data_path}/qa_{self.product_id}.csv", index=False)
            logger.info(
                f"Q&A data for product ID {self.product_id} saved to file...")
        except Exception as e:
            logger.error(
                f"Failed to save Q&A data for product ID {self.product_id}. Error: {e}...")

    def crawl_page(self, page):
        """Crawl data for a specific page.

        Args:
            page (int): The page number.

        Returns:
            None
        """
        # response = self.get_qa(page)
        # qa_data = self.parse_qa(response)
        # with self.qa_data_lock:
        #     self.qa_data = pd.concat(
        #         [self.qa_data, qa_data], ignore_index=True)

        # time.sleep(random.uniform(3, 5))
        response = self.get_qa(page)
        if not response:
            logger.warning(f"No response received for page {page}. Skipping...")
            return
        qa_data = self.parse_qa(response)
        if qa_data.empty:
            logger.warning(f"No Q&A data found for page {page}. Skipping...")
            return
        with self.qa_data_lock:
            self.qa_data = pd.concat(
                [self.qa_data, qa_data], ignore_index=True)

        time.sleep(random.uniform(3, 5))

    def start_crawling(self, product_id):
        """
        Start scraping product question and answer (Q&A) data.

        Args:
            product_id (str): ID of the product to fetch Q&A for.
            
        Returns:
            None
        """
        # Update the product_id attribute
        self.product_id = product_id

        logger.info(
            f"Start scraping Q&A data for product ID {self.product_id}...")
        
        # Clear qa_data
        self.qa_data = pd.DataFrame(
            columns=['id', 'question_content', 'product_id', 'created_time', 'answer_id',
                    'answer_content', 'answer_created_time', 'location'])
        
        # Create a thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for page in range(1, self.pages + 1):
                executor.submit(self.crawl_page, page)

        logger.info(
            f"Scraping Q&A data for product ID {self.product_id} completed...")
        # Save the data
        self.save_data(self.qa_data)
