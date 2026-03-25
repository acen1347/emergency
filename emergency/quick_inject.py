import sqlite3
import datetime
import random
import os

# 数据库路径
DB_PATH = "d:/FireAgent_Competition/fire_agent.db"

def inject_data():
    if not os.path.exists(DB_PATH):
        print(f"数据库不存在: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 清空旧数据
    cursor.execute("DELETE FROM fire_events")
    
    locations = [
        ("北京朝阳大悦城", "人员密集区"),
        ("海淀中关村软件园", "办公区"),
        ("丰台新发地市场", "人员密集区"),
        ("通州潞河医院", "人员密集区"),
        ("石景山首钢园", "易燃易爆区"),
        ("大兴国际机场货运站", "易燃易爆区"),
        ("昌平天通苑北一区", "普通居民区"),
        ("顺义燕京啤酒厂", "易燃易爆区"),
        ("西单更新场", "人员密集区"),
        ("望京 SOHO", "办公区")
    ]

    now = datetime.datetime.now()
    
    for i in range(15):
        loc, scene = random.choice(locations)
        severity = random.randint(1, 5)
        # 随机生成过去 24 小时内的时间
        offset = random.randint(0, 24 * 60)
        alarm_time = (now - datetime.timedelta(minutes=offset)).strftime("%Y-%m-%d %H:%M:%S")
        status = "completed" if random.random() > 0.3 else "processing"
        
        cursor.execute('''
            INSERT INTO fire_events (location, alarm_time, severity, status, scene)
            VALUES (?, ?, ?, ?, ?)
        ''', (loc, alarm_time, severity, status, scene))

    conn.commit()
    conn.close()
    print("✅ 成功注入 15 条高质量模拟数据")

if __name__ == "__main__":
    inject_data()
