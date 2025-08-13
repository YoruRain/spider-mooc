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

def fetch_data_from_db(connection, where=None):
    """从数据库获取所有评论数据"""
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    query = """
    SELECT * FROM comments
    """
    if where:
        query += f" WHERE {where}"
    cursor.execute(query)
    return cursor.fetchall()

def transform_data(data, categories=None):
    """将数据库数据转换为指定格式的字典"""
    result = {}
    
    categories = categories or  [
        "工学", "理学", "外语", "管理学", "医药卫生",
        "法学", "教育教学", "计算机", "文学文化", "艺术学", 
        "经济学", "农林园艺", "哲学", "心理学", "历史"
    ]

    for row in data:
        category = row['category'].split()
        if all(c not in categories for c in category):
            continue

        # 创建键名：学校名-课程名
        key = f"{row['school']}-{row['course_name']}"
        
        # 如果这个课程还没有在结果字典中，创建新的课程条目
        if key not in result:
            category = row['category'].split()
            exact_category = ''
            special = ''
            if len(category) == 1:
                exact_category = category[0]
            elif len(category) > 1:
                for c in category:
                    if c in categories:
                        exact_category = c
                        category.remove(c)
                        special = ' '.join(category)
                        break
            result[key] = {
                "category": exact_category,
                "special": special,
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
    
    course_category_dict = {
        "自然科学": ["理学", "工学", "计算机", "医药卫生", "农林园艺"], 
        "社会科学": ["管理学", "法学", "经济学", "教育教学", "心理学"], 
        "人文艺术": ["文学文化", "艺术学", "哲学", "历史", "外语"]
    }

    try:
        for category, sub_categories in course_category_dict.items():
            patten = '|'.join(sub_categories)
            data = fetch_data_from_db(connection, f"category REGEXP '{patten}'")
            transformed_data = transform_data(data, sub_categories)
            save_to_json(transformed_data, f"collected_data/{category}({','.join(sub_categories)}).json")

            print(f"{category} 课程的数据已成功转换为JSON文件！")

        # # 获取数据
        # data = fetch_data_from_db(connection)
        
        # # 转换数据格式
        # transformed_data = transform_data(data)
        
        # # 保存为JSON文件
        # save_to_json(transformed_data)
        
    except Exception as e:
        print(f"处理过程中出现错误: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    main()
