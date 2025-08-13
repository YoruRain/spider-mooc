'''
@Description: The saver file 
@Author: Chase Huang
@Date: 2019-05-30 09:39:29
@LastEditTime: 2019-06-20 09:36:14
'''
# import MySQLdb
import pymysql
import json
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/spider.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 确保数据目录存在
Path('data').mkdir(exist_ok=True)

with open("config.json", 'r', encoding='utf-8') as f:
    config = json.load(f)


def saver(school, category, course_name, teacher, url, userid_list, names_list,
          comments_list, created_time_list, course_times_list, voteup_list,
          rating_list):
    '''
    @description: Save the comments info to mysql
    @param All field in mysql; {"conn,cursor": the code to use mysql}
    @return: None
    '''
    # 准备批量插入的数据
    values_list = []
    for i in range(len(names_list)):
        values = [
            school, category, course_name, teacher, url, 
            userid_list[i], names_list[i], comments_list[i],
            created_time_list[i], course_times_list[i], 
            voteup_list[i], rating_list[i]
        ]
        values_list.append(values)

    cols = [
        "school", "category", "course_name", "teacher", "url", 
        "userid", "author_name", "comments",
        "created_time", "course_times", "voteup", "rating"
    ]

    insert_sql = f"""INSERT INTO comments({", ".join(cols)}) 
    VALUES ({", ".join(["%s"] * len(cols))})"""
    
    try:
        with pymysql.connect(**config["database"]) as conn:
            with conn.cursor() as cursor:
                cursor.executemany(insert_sql, values_list)
                conn.commit()
                logging.info(f"课程 {course_name} 的 {len(names_list)} 条评论批量保存成功")
    
    except Exception as e:
        logging.error(f"将课程 {course_name} 的评论批量保存到数据库时发生错误: {e}")
