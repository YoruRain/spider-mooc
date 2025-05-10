import pymysql
import json
from datetime import datetime

def connect_to_database():
    """连接到MySQL数据库"""
    try:
        with open("config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        connection = pymysql.connect(**config["database"])
        return connection
    except Exception as err:
        print(f"数据库连接错误: {err}")
        return None

def fetch_data_from_db(connection):
    """从数据库获取所有评论数据"""
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    query = """
    SELECT * FROM comments
    """
    cursor.execute(query)
    return cursor.fetchall()

def transform_data(data):
    """将数据库数据转换为指定格式的字典"""
    result = {}
    
    for row in data:
        # 创建键名：学校名-课程名
        key = f"{row['school']}-{row['course_name']}"
        
        # 如果这个课程还没有在结果字典中，创建新的课程条目
        if key not in result:
            result[key] = {
                "category": row['category'],
                "teacher": row['teacher'],
                "url": row['url'],
                "comments": []
            }
        
        # 添加评论信息
        comment = {
            "userid": row['userid'],
            "author_name": row['author_name'],
            "comments": row['comments'],
            "course_times": row['course_times'],
            "voteup": row['voteup'],
            "rating": row['rating']
        }
        
        result[key]["comments"].append(comment)
    
    return result

def save_to_json(data, filename="course_comments.json"):
    """将数据保存为JSON文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def main():
    # 连接数据库
    connection = connect_to_database()
    if not connection:
        return
    
    try:
        # 获取数据
        data = fetch_data_from_db(connection)
        
        # 转换数据格式
        transformed_data = transform_data(data)
        
        # 保存为JSON文件
        save_to_json(transformed_data)
        print("数据已成功转换为JSON文件！")
        
    except Exception as e:
        print(f"处理过程中出现错误: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    main()
