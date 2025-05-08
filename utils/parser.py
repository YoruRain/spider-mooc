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


# get all courses url from category page
def get_courses_url(course_url, driver):
    '''
    @description: get the course url from category page
    @param {"course_url":category_url,"driver":chrome driver} 
    @return: link_list
    '''
    link_list = []
    driver.get(course_url)
    time.sleep(5)  # 增加等待时间
    
    try:
        # 使用显式等待查找关闭按钮
        close_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "u-icon-close"))
        )
        close_button.click()
    except Exception:
        pass

    while True:
        try:
            # get the page source
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            link_area = soup.find_all('div', {'class': 'cnt f-pr'})
            for tags in link_area:
                tag = tags.find_all('a')
                for a in tag:
                    link = a.get('href')
                    try:
                        if link and 'www' in link and 'http' not in link:
                            link = 'https:' + link
                            link_list.append(link)
                    except Exception:
                        continue

            # 使用显式等待查找下一页按钮
            next_page = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.ux-pager_btn.ux-pager_btn__next a"))
            )
            
            # 检查是否是最后一页
            if "th-bk-disable-gh" in next_page.get_attribute("class"):
                break
                
            next_page.click()
            time.sleep(random.randint(2, 4))  # 增加随机等待时间

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            break

    link_list = list(set(link_list))
    return link_list


def paser_comments(url, category, driver):
    '''
    @description: get the course comments info from the course page
    @param {"url":course_url,"category":course_tag,"driver":chrome driver} 
    @return: category, course_name, teacher, url, names_list, comments_list, created_time_list, course_times_list, voteup_list, rating_list
    '''
    driver.get(url)
    time.sleep(5)  # 增加等待时间
    
    try:
        # 使用显式等待查找评论按钮
        find_comments = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "review-tag-button"))
        )
        find_comments.click()
        time.sleep(2)
    except Exception as e:
        print(f"Error clicking comment button: {str(e)}")
        return None

    # get the course name and teacher info
    info = pq(driver.page_source)
    course_name = info(".course-title.f-ib.f-vam").text()
    teacher = info(".cnt.f-fl").text().replace("\n", " ")

    # init the parameter list
    userid_list = []  # userid_list
    names_list = []  # nikename
    comments_list = []  # comments
    created_time_list = []  # created_time
    course_times_list = []  # course_times
    voteup_list = []  # voteup
    rating_list = []  # rating

    while True:
        try:
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # use bs4 to locate the comments
            content = soup.find_all('div', {
                'class': 'ux-mooc-comment-course-comment_comment-list_item_body'
            })

            if not content:  # 如果没有找到评论内容，退出循环
                break

            for ctt in content:
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
                    created_time_list.append(ct.text)
                for cts in course_times:
                    course_times_list.append(cts.text)
                for vt in voteup:
                    voteup_list.append(vt.text.strip('\n'))
                for r in rating:
                    rating_list.append(str(len(r)))

            # 使用显式等待查找下一页按钮
            next_page = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.ux-pager_btn.ux-pager_btn__next a"))
            )
            
            # 检查是否是最后一页
            if "th-bk-disable-gh" in next_page.get_attribute("class"):
                break
                
            next_page.click()
            time.sleep(random.randint(2, 4))  # 增加随机等待时间

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            break

    return category, course_name, teacher, url, userid_list, names_list, comments_list, created_time_list, course_times_list, voteup_list, rating_list
