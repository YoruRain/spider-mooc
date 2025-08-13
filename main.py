'''
@Description: The main file
@Author: Chase Huang
@Date: 2019-05-30 09:29:39
@LastEditTime: 2019-06-21 06:53:21
'''
# import MySQLdb
import pymysql
from selenium import webdriver
from utils.parser import get_courses_url, parse_comments, get_all_schools_url, get_school_name_from_course_url
from utils.saver import saver
from selenium.webdriver.chrome.service import Service
import json
import random

with open('config.json', 'r') as f:
    config = json.load(f)

def main0():
    '''
    @description: This is the main function to set the database info and load the webdriver, then start the crawler
    '''
    database_config = config['database']
    host = database_config['host']
    user = database_config['user']
    password = database_config['password']
    db = database_config['db']
    charset = database_config['charset']

    conn = MySQLdb.connect(
        host, user, password, db, charset=charset, use_unicode=True)
    cursor = conn.cursor()
    # driver = webdriver.Chrome(executable_path=r"drivers/chromedriver.exe")

    # 使用Chrome浏览器
    service = Service(executable_path=r"drivers/chromedriver.exe")
    driver = webdriver.Chrome(service=service)
    driver.maximize_window()

    # 读取学校URL
    school_dict = get_all_schools_url(driver)

    for school_name, school_url in school_dict.items():
        link_list = get_courses_url(school_url, driver)
        for url in link_list:
            try:
                comment_info = [school_name]
                # (university, category, course_name, teacher, url, userid_list, names_list, comments_list, created_time_list, course_times_list, voteup_list, rating_list) = paser_comments(url, driver)
                comment_info.extend(parse_comments(url, driver))
                if comment_info:
                    saver(*comment_info, conn, cursor)
            
                with open("course_done.txt", 'a', encoding='utf-8') as f:
                    f.write(f"{url}\n")

            except Exception:
                continue

    driver.quit()
    conn.close()

    print("\nALL Done...")


def main():
    service = Service(executable_path=r"drivers/chromedriver.exe")
    driver = webdriver.Chrome(service=service)
    driver.maximize_window()

    # 读取已处理的课程URL
    processed_urls = set()
    try:
        with open("data/processed_urls.txt", 'r', encoding='utf-8') as f:
            processed_urls = set(line.strip() for line in f)
    except FileNotFoundError:
        pass

    # 读取所有课程URL
    with open("data/course_urls.txt", 'r', encoding='utf-8') as f:
        urls = f.readlines()
    course_urls = [url.strip() for url in urls if url.strip() not in processed_urls]

    print(f"总课程数: {len(urls)}, 已处理: {len(processed_urls)}, 待处理: {len(course_urls)}")

    # 创建进度记录文件
    with open("data/processed_urls.txt", 'a', encoding='utf-8') as f:
        processed_count = 0
        while course_urls:  # 当还有未处理的URL时继续
            # 随机选择一个URL
            url = random.choice(course_urls)
            course_urls.remove(url)  # 从待处理列表中移除
            # url = "https://www.icourse163.org/course/cupl-1002606068"
            try:
                school_name = get_school_name_from_course_url(url)
                comment_info = [school_name]
                comment_info.extend(parse_comments(url, driver))
                
                if len(comment_info) == 2:
                    print(f"跳过课程 {school_name}-{comment_info[1]}")
                elif comment_info:
                    saver(*comment_info)
                
                # 记录已处理的URL
                f.write(f"{url}\n")
                f.flush()  # 确保立即写入文件
                
                processed_count += 1
                # 每处理10个课程打印一次进度
                if processed_count % 10 == 0:
                    print(f"进度: {processed_count}/{len(urls)} ({(processed_count/len(urls)*100):.2f}%)")
                
            except Exception as e:
                print(f"处理课程 {url} 时发生错误: {str(e)}")
                continue

    driver.quit()
    print("\n爬取完成！")

if __name__ == "__main__":
    main()