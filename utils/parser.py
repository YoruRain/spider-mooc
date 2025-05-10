'''
@Description: The spider file 
@Author: Chase Huang
@Date: 2019-05-30 09:39:37
@LastEditTime: 2019-06-20 10:15:21
'''
import time
import random
import MySQLdb
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
from bs4 import BeautifulSoup
import json
from selenium.webdriver.chrome.service import Service
import sys
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import os
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('spider.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 配置参数
CONFIG = {
    'WAIT_TIME': 5,
    'RANDOM_WAIT_MIN': 2,
    'RANDOM_WAIT_MAX': 10,
    'MAX_RETRIES': 3,
    'DATA_DIR': 'data'
}

# 确保数据目录存在
Path(CONFIG['DATA_DIR']).mkdir(exist_ok=True)

# get all courses url from category page
def get_courses_url(course_url: str, driver: webdriver.Chrome) -> List[str]:
    '''
    @description: get the course url from category page
    @param course_url: category_url
    @param driver: chrome driver
    @return: list of course urls
    '''
    link_list = []
    retry_count = 0
    
    while retry_count < CONFIG['MAX_RETRIES']:
        try:
            driver.get(course_url)
            time.sleep(CONFIG['WAIT_TIME'])
            
            # 尝试关闭弹窗
            try:
                close_button = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "u-icon-close"))
                )
                close_button.click()
            except Exception as e:
                logging.debug(f"没有找到关闭按钮或已关闭: {str(e)}")

            while True:
                try:
                    html = driver.page_source
                    soup = BeautifulSoup(html, 'html.parser')
                    link_area = soup.find_all('div', {'class': 'um-spoc-course-list_wrap'})
                    
                    for tags in link_area:
                        tag = tags.find_all('a')
                        for a in tag:
                            link = a.get('href')
                            if link and 'www' in link and 'http' not in link:
                                link = 'https:' + link
                                if link not in link_list:  # 避免重复
                                    link_list.append(link)

                    logging.info(f"已获取 {course_url} 的 {len(link_list)} 门课程的 URL")

                    next_page = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "a.zbtn.znxt"))
                    )
                    
                    if "zbtn znxt js-disabled" in next_page.get_attribute("class"):
                        break
                        
                    next_page.click()
                    time.sleep(random.randint(CONFIG['RANDOM_WAIT_MIN'], CONFIG['RANDOM_WAIT_MAX']))

                except Exception as e:
                    logging.error(f"获取课程URL时发生错误: {str(e)}")
                    break

            # 如果成功获取数据，跳出重试循环
            break

        except Exception as e:
            retry_count += 1
            logging.error(f"第 {retry_count} 次尝试获取课程URL失败: {str(e)}")
            if retry_count == CONFIG['MAX_RETRIES']:
                logging.error(f"达到最大重试次数，放弃获取 {course_url} 的课程URL")
                return []

    # 保存课程URL到文件
    if link_list:
        try:
            course_file = Path(CONFIG['DATA_DIR']) / 'course_url.txt'
            with open(course_file, 'a', encoding='utf-8') as f:
                for link in link_list:
                    f.write(f"{link}\n")
            logging.info(f"成功保存 {len(link_list)} 个课程URL到文件")
        except Exception as e:
            logging.error(f"保存课程URL到文件时发生错误: {str(e)}")

    return link_list


def parse_comments(url: str, driver: webdriver.Chrome) -> Optional[Tuple]:
    '''
    @description: get the course comments info from the course page
    @param url: course_url
    @param driver: chrome driver
    @return: tuple of (category, course_name, teacher, url, userid_list, names_list, 
            comments_list, created_time_list, course_times_list, voteup_list, rating_list)
    '''
    retry_count = 0
    while retry_count < CONFIG['MAX_RETRIES']:
        try:
            driver.get(url)
            time.sleep(CONFIG['WAIT_TIME'])
            
            try:
                find_comments = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "review-tag-button"))
                )
                find_comments.click()
                time.sleep(2)
            except Exception as e:
                logging.error(f"点击评论按钮失败: {str(e)}")
                retry_count += 1
                continue

            # 获取课程基本信息
            info = pq(driver.page_source)
            category = info(".breadcrumb_item.sub-category").text()
            course_name = info(".course-title.f-ib.f-vam").text()
            teacher = info(".cnt.f-fl").text().replace("\n", " ")

            # 初始化参数列表
            userid_list = []
            names_list = []
            comments_list = []
            created_time_list = []
            course_times_list = []
            voteup_list = []
            rating_list = []

            while True:
                try:
                    page_source = driver.page_source
                    soup = BeautifulSoup(page_source, 'html.parser')
                    
                    content = soup.find_all('div', {
                        'class': 'ux-mooc-comment-course-comment_comment-list_item_body'
                    })

                    if not content:
                        logging.info(f"课程 {course_name} 没有更多评论")
                        break

                    for ctt in content:
                        try:
                            author_name = ctt.find_all(
                                'a', {
                                    'class': 'primary-link ux-mooc-comment-course-comment_comment-list_item_body_user-info_name'
                                })
                            comments = ctt.find_all(
                                'div', {
                                    'class': 'ux-mooc-comment-course-comment_comment-list_item_body_content'
                                })
                            created_time = ctt.find_all(
                                'div', {
                                    'class': 'ux-mooc-comment-course-comment_comment-list_item_body_comment-info_time'
                                })
                            course_times = ctt.find_all(
                                'div', {
                                    'class': 'ux-mooc-comment-course-comment_comment-list_item_body_comment-info_term-sign'
                                })
                            voteup = ctt.find_all('span', {'primary-link'})
                            rating = ctt.find_all('div', {"star-point"})

                            for userid in author_name:
                                userid_list.append(userid.get('href').split('=')[-1])
                            for name in author_name:
                                names_list.append(name.text)
                            for comment in comments:
                                comments_list.append(comment.text.strip('\n'))
                            for ct in created_time:
                                ct_time = ct.text.split(' ')[1]
                                created_time_list.append(ct_time)
                            for cts in course_times:
                                course_times_list.append(cts.text.strip())
                            for vt in voteup:
                                voteup_list.append(vt.text.strip('\n'))
                            for r in rating:
                                stars = r.find_all('i', {'class': 'star ux-icon-custom-rating-favorite'})
                                rating_list.append(str(len(stars)))
                        except Exception as e:
                            logging.error(f"解析评论数据时发生错误: {str(e)}")
                            continue

                    try:
                        next_page = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "li.ux-pager_btn__next > a"))
                        )
                        
                        # 检查按钮是否已禁用
                        if "th-bk-disable-gh" in next_page.get_attribute("class"):
                            logging.info("已到达最后一页")
                            break
                            
                        next_page.click()
                        time.sleep(random.randint(CONFIG['RANDOM_WAIT_MIN'], CONFIG['RANDOM_WAIT_MAX']))
                    except Exception as e:
                        logging.info("已到达最后一页")
                        break

                except Exception as e:
                    logging.error(f"获取评论页面时发生错误: {str(e)}")
                    break

            return (category, course_name, teacher, url, userid_list, names_list, 
                   comments_list, created_time_list, course_times_list, 
                   voteup_list, rating_list)

        except Exception as e:
            retry_count += 1
            logging.error(f"第 {retry_count} 次尝试获取评论失败: {str(e)}")
            if retry_count == CONFIG['MAX_RETRIES']:
                logging.error(f"达到最大重试次数，放弃获取 {url} 的评论")
                return None

    return None


def get_all_schools_url(driver):
    '''
    @description: 获取所有合作高校的URL信息
    @param {"driver": chrome driver} 
    @return: 包含高校名称和URL的字典
    '''
    try:
        with open('school_url.json', 'r') as f:
            school_dict = json.load(f)
            if school_dict:
                return school_dict
    except FileNotFoundError:
        pass
    choice = input("未找到指定高校 URL 文件。是否需要重新获取高校URL？(y/n): ")
    if choice != 'y':
        sys.exit()
    school_dict = {}
    url = 'https://www.icourse163.org/university/view/all.htm#/'
    driver.get(url)
    time.sleep(5)  # 等待页面加载
    
    try:
        # 使用显式等待查找关闭按钮
        close_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "u-icon-close"))
        )
        close_button.click()
    except Exception:
        pass

    # 获取页面源码
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    # 查找所有高校链接
    school_links = soup.find_all('a', {'class': 'u-usity f-fl all-school-card'})
    
    for link in school_links:
        school_name = link.find('img')['alt']  # 获取高校名称
        school_url = 'https://www.icourse163.org' + link['href'] + '#/c'  # 构建完整URL
        school_dict[school_name] = school_url
    
    return school_dict

def get_school_name_from_course_url(course_url):
    """
    从课程URL中提取学校名称
    
    Args:
        course_url (str): 课程URL，例如 https://www.icourse163.org/course/PKU-1205827823
        
    Returns:
        str: 学校名称，如果未找到则返回None
    """
    # 从URL中提取学校代码
    match = re.search(r'course/([A-Z]+)-', course_url)
    if not match:
        return None
    
    school_code = match.group(1)
    
    # 读取school_url.json文件
    with open('data/school_url.json', 'r', encoding='utf-8') as f:
        school_dict = json.load(f)
    
    # 遍历学校字典，查找匹配的学校代码
    for school_name, school_url in school_dict.items():
        if school_code in school_url:
            return school_name
    
    return None



if __name__ == "__main__":
    driver = None
    try:
        service = Service(executable_path=r"drivers/chromedriver.exe")
        driver = webdriver.Chrome(service=service)
        
        school_dict = get_all_schools_url(driver)
        if not school_dict:
            logging.error("获取学校列表失败")
            sys.exit(1)
            
        for school_name, school_url in school_dict.items():
            try:
                logging.info(f"开始获取学校 {school_name} 的课程")
                link_list = get_courses_url(school_url, driver)
                
                if not link_list:
                    logging.warning(f"学校 {school_name} 没有获取到课程URL")
                    continue
                    
                for course_url in link_list:
                    try:
                        logging.info(f"开始获取课程 {course_url} 的评论")
                        result = parse_comments(course_url, driver)
                        if result is None:
                            logging.warning(f"获取课程 {course_url} 的评论失败")
                            continue
                    except Exception as e:
                        logging.error(f"处理课程 {course_url} 时发生错误: {str(e)}")
                        continue
                        
            except Exception as e:
                logging.error(f"处理学校 {school_name} 时发生错误: {str(e)}")
                continue
                
    except Exception as e:
        logging.error(f"程序运行出错: {str(e)}")
        sys.exit(1)
        
    finally:
        if driver:
            try:
                driver.quit()
                logging.info("成功关闭WebDriver")
            except Exception as e:
                logging.error(f"关闭WebDriver时发生错误: {str(e)}")
