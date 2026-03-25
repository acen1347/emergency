# delete_and_reset.py - 数据清理+ID重置工具
import sqlite3
from config import DB_FILE

def delete_fire_event_by_id(event_id: int):
    """删除指定ID的火灾记录"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 先查询记录是否存在
        cursor.execute("SELECT * FROM fire_events WHERE id = ?", (event_id,))
        record = cursor.fetchone()
        if not record:
            print(f"❌ 未找到ID为 {event_id} 的记录")
            return False
        
        # 执行删除
        cursor.execute("DELETE FROM fire_events WHERE id = ?", (event_id,))
        conn.commit()
        print(f"✅ 成功删除ID为 {event_id} 的记录")
        return True
    except Exception as e:
        print(f"❌ 删除失败：{str(e)}")
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def reset_auto_increment():
    """重置fire_events表的自增ID，让新数据从1开始"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 步骤1：备份当前数据
        cursor.execute("CREATE TABLE IF NOT EXISTS fire_events_temp AS SELECT * FROM fire_events ORDER BY id ASC")
        
        # 步骤2：删除原表并重建
        cursor.execute("DROP TABLE fire_events")
        cursor.execute("""
            CREATE TABLE fire_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location TEXT NOT NULL,
                alarm_time TEXT NOT NULL,
                severity INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                scene TEXT DEFAULT '普通居民区'
            )
        """)
        
        # 步骤3：恢复数据（自增ID重新从1开始）
        cursor.execute("""
            INSERT INTO fire_events (location, alarm_time, severity, status, scene)
            SELECT location, alarm_time, severity, status, scene FROM fire_events_temp
        """)
        
        # 步骤4：清理临时表+重置自增计数器
        cursor.execute("DROP TABLE fire_events_temp")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'fire_events'")
        
        conn.commit()
        print("✅ 自增ID已重置，新数据将从1开始！")
        return True
    except Exception as e:
        print(f"❌ 重置自增ID失败：{str(e)}")
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def show_all_events():
    """查看当前所有记录（验证操作结果）"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM fire_events ORDER BY id ASC")
        columns = [desc[0] for desc in cursor.description]
        events = [dict(zip(columns, row)) for row in cursor.fetchall()]
        print("\n📄 当前数据库所有记录：")
        for idx, event in enumerate(events, 1):
            print(f"{idx}. {event}")
        return events
    except Exception as e:
        print(f"❌ 查询失败：{str(e)}")
        return []
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# 主执行逻辑
if __name__ == "__main__":
    # 1. 删除指定ID（可修改为需要删除的ID）
    delete_fire_event_by_id(4)
    
    # 2. 重置自增ID
    reset_auto_increment()
    
    # 3. 查看操作结果
    show_all_events()
