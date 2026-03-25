# init_db.py - 初始化数据库（修复scene字段缺失）
import sqlite3
import os

def init_database():
    """初始化火灾事件数据库，包含scene字段"""
    # 数据库文件路径（当前目录）
    db_path = "fire_agent.db"
    
    # 如果数据库已存在，先删除（确保表结构最新）
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # 连接数据库（不存在则创建）
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建火灾事件表（新增scene字段）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fire_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT NOT NULL,       -- 火灾地点
            alarm_time TEXT NOT NULL,    -- 报警时间
            severity INTEGER NOT NULL,   -- 火灾等级（1-5）
            status TEXT NOT NULL,        -- 事件状态（pending/processing/completed）
            scene TEXT NOT NULL DEFAULT '普通居民区'  -- 火灾场景（新增字段）
        )
    ''')
    
    # 提交并关闭连接
    conn.commit()
    conn.close()
    
    print("✅ 消防数据库初始化完成！")
    print(f"✅ 表结构已更新，包含scene字段，数据库路径：{os.path.abspath(db_path)}")

def save_fire_event(location, severity, scene="普通居民区"):
    """保存火灾事件到数据库（适配scene字段）"""
    try:
        from datetime import datetime
        db_path = "fire_agent.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取当前时间作为报警时间
        alarm_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 插入数据（包含scene字段）
        cursor.execute('''
            INSERT INTO fire_events (location, alarm_time, severity, status, scene)
            VALUES (?, ?, ?, ?, ?)
        ''', (location, alarm_time, severity, "processing", scene))
        
        # 获取自增的event_id
        event_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        print(f"✅ 事件写入成功！event_id={event_id}，场景={scene}")
        return event_id
    
    except Exception as e:
        print(f"❌ 保存事件失败：{str(e)}")
        return None

# 执行初始化
if __name__ == "__main__":
    init_database()