# -*- coding: utf-8  -*-
# @Author  : Yu Ching San
# @Email   : zhgyqc@163.com
# @Time    : 2023/8/10 11:50
# @File    : main.py
# @Software: PyCharm
import json
import os
import random
import time

from loguru import logger

from com_spider import JDCommentSpider
from qa_spider import JDQASpider

import config


def crawl_comments_and_qa(ids_collection_dir, output_dir):
    """Crawl comments and Q&A for the products in the specified directory.

    Args:
        ids_collection_dir (str): Path to the directory containing the JSON files.
        output_dir (str): Path to the directory to store the output files.

    Returns:
        None
    """
    # Initialize the spiders
    comment_spider = JDCommentSpider()
    qa_spider = JDQASpider()
    resume_checkpoint = './resume_checkpoint.txt'

    # Check if the provided path exists
    if not os.path.exists(ids_collection_dir):
        logger.error(f"Error: Directory '{ids_collection_dir}' not found.")
        return

    # Create the output directory if it does not exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Get the list of files to process
    files_to_process = os.listdir(ids_collection_dir)

    # If resume_checkpoint is provided, find the index to resume from
    if os.path.exists(resume_checkpoint):
        try:
            with open(resume_checkpoint, 'r') as checkpoint_file:
                checkpoint_content = checkpoint_file.readlines()
            checkpoint_content = list(
                map(lambda x: x.strip("\n"), checkpoint_content))
            print(checkpoint_content)

            # Remove the files that have already been processed
            checkpoint_set = set(checkpoint_content)
            files_to_process = list(
                filter(lambda x: x not in checkpoint_set, files_to_process))

        except ValueError:
            logger.error(
                f"Checkpoint file '{resume_checkpoint}' not found.")
            return

    # Iterate over each file in the directory
    for filename in files_to_process:
        file_path = os.path.join(ids_collection_dir, filename)

        # Check if the file is a JSON file
        if os.path.isfile(file_path) and filename.endswith('.json'):
            try:
                # Load the JSON content
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)

                # Get the list of files in the output directory
                output_files = os.listdir(output_dir)
                # Remove the file extension from the filenames
                output_files = [file.split('_')[1].split(
                    '.')[0] for file in output_files if file.endswith('.csv')]

                # Iterate over each product ID in the JSON
                for product_info in list(data.values())[0]:
                    product_id = product_info["sku"]

                    # Skip if the product ID has already been processed
                    if product_id in output_files:
                        continue
                    # Crawl comments for the current product ID
                    comment_spider.start_crawling(product_id)

                    # # Crawl Q&A for the current product ID
                    # qa_spider.start_crawling(product_id)

                    # Sleep for a random amount of time between 0.5 to 3 minutes
                    time.sleep(random.randint(30, 180))

                # Save the checkpoint after successfully processing each file
                with open(resume_checkpoint, 'a') as checkpoint_file:
                    checkpoint_file.write(filename + "\n")

            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.error(f"Error processing file: {file_path}, {str(e)}")


if __name__ == '__main__':

    IDS_COLLECTION_DIR = '.\ids_collection\collection_01'
    crawl_comments_and_qa(
        ids_collection_dir=IDS_COLLECTION_DIR, output_dir=config.DATA_PATH)
