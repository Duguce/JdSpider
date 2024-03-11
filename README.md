# JdSpider

京东评论&问答数据爬虫：根据商品Id实现对京东平台上的评论内容（目前仅支持爬取单个商品前100页的评论内容）及商品问答模块的问题数据

## 项目结构

```
│  com_spider.py               # 京东评论爬取模块
│  config.py                   # 配置文件
│  main.py                     # 主程序入口（批量爬取评论和问答内容）
│  qa_spider.py                # 问答爬虫模块
│  README.md                   # 项目说明文档
│  requirements.txt            # 依赖库配置
│  search_spider.py            # 搜索爬虫模块（根据关键词批量爬取商品Id）
│
├─drivers                      # 驱动文件目录
│      chromedriver.exe        # Chrome浏览器驱动
│      geckodriver.exe         # Firefox浏览器驱动
│
├─ids_collection               # 商品ID存储目录
├─output                       # 爬取评论和问答内容存储目录

```

## 快速开始

1. 准备环境

   - `conda create -n jd_spider python=3.8.18`

   - `conda activate jd_spider`

   - `pip install -r requirements.txt`

2. 配置

   - 重命名[example_config.py](./example_config.py)为`config.py`
   - 在`config.py`配置相关信息

3. 运行

   - 运行[search_spider.py](./search_spider.py)获取商品ID
   - 运行[main.py](./main.py)收集商品评论和问答内容

## 待做功能

- [x] 根据关键词从京东主页批量抓取商品ID；
- [x] 批量抓取商品评论&问答数据逻辑；
- [x] `main.py`模块实现断点续爬；
- [ ] `search_spider.py`模块中登录时的滑块验证实现自动化；
- [x] 优化`com_spider.py`和`qa_spider.py`模块中的存储逻辑；
