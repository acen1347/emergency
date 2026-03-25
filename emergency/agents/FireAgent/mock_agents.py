# mock_agents.py - 消防智能体API接口（完整修复版）
from fastapi import FastAPI, APIRouter, Query
from pydantic import BaseModel
import datetime
from datetime import timedelta
import random
import sqlite3
import os

# 初始化FastAPI应用
app = FastAPI(
    title="消防智能体API",
    description="城市级多智能体协同应急调度系统 - 消防智能体模块",
    version="1.0.0"
)
router = APIRouter()

# ==================== 数据模型定义 ====================
class AgentMessage(BaseModel):
    """多智能体通信的标准化消息模型"""
    sender: str          # 发送方智能体名称（如weather_agent）
    receiver: str        # 接收方智能体名称（必须为fire_agent）
    message_type: str    # 消息类型：data/proposal/response
    content: dict        # 消息内容（结构化数据）
    timestamp: str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 消息时间

# ==================== 全局缓存（存储其他智能体数据） ====================
agent_cache = {
    "weather_data": {},   # 气象数据缓存
    "traffic_data": {},   # 交通数据缓存
    "medical_response": {}, # 医疗智能体响应缓存
    "security_response": {} # 安防智能体响应缓存
}

# ==================== 多智能体协同接口 ====================
@router.post("/api/agent/receive", summary="接收其他智能体消息")
def receive_agent_message(message: AgentMessage):
    """
    接收气象/交通/医疗/安防等智能体的消息并缓存
    """
    try:
        # 验证接收方
        if message.receiver != "fire_agent":
            return {
                "code": 400,
                "msg": f"接收方错误，当前智能体为fire_agent，收到的接收方为{message.receiver}"
            }
        
        # 根据发送方缓存数据
        if message.sender == "weather_agent":
            agent_cache["weather_data"] = message.content
            msg = "✅ 气象数据已接收并缓存"
        elif message.sender == "traffic_agent":
            agent_cache["traffic_data"] = message.content
            msg = "✅ 交通数据已接收并缓存"
        elif message.sender == "medical_agent":
            agent_cache["medical_response"] = message.content
            msg = "✅ 医疗智能体响应已接收并缓存"
        elif message.sender == "security_agent":
            agent_cache["security_response"] = message.content
            msg = "✅ 安防智能体响应已接收并缓存"
        else:
            msg = f"✅ 未知智能体({message.sender})数据已接收"
        
        return {
            "code": 200,
            "msg": msg,
            "data": message.dict()
        }
    except Exception as e:
        return {
            "code": 500,
            "msg": f"接收消息失败：{str(e)}",
            "data": {}
        }

@router.get("/api/agent/send", summary="向其他智能体发送协同请求")
def send_agent_request(
    receiver: str = Query(..., description="目标智能体名称"),
    severity: int = Query(..., ge=1, le=5, description="火灾等级1-5"),
    location: str = Query(..., description="火灾地点")
):
    """
    向医疗/安防/气象/交通智能体发送救援请求/数据查询
    """
    try:
        # 支持的目标智能体列表
        supported_agents = ["weather_agent", "traffic_agent", "medical_agent", "security_agent"]
        if receiver not in supported_agents:
            return {
                "code": 400,
                "msg": f"不支持的智能体：{receiver}，支持的列表：{supported_agents}"
            }
        
        # 构造标准化请求消息
        request_message = {
            "sender": "fire_agent",
            "receiver": receiver,
            "message_type": "proposal",
            "content": {
                "fire_location": location,
                "fire_severity": severity,
                "request_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 模拟发送（无实际网络请求，仅返回请求内容）
        return {
            "code": 503,  # 模拟目标智能体未启动
            "msg": f"❌ {receiver}智能体服务未启动（端口{8001 + supported_agents.index(receiver)}），请先启动该服务",
            "request_data": request_message
        }
    except Exception as e:
        return {
            "code": 500,
            "msg": f"发送请求失败：{str(e)}",
            "request_data": {}
        }

# ==================== 核心业务接口 ====================
@router.get("/api/process_fire_event", summary="处理火灾事件（核心接口）")
def process_fire_event(
    location: str = Query(..., description="火灾地点"),
    severity: int = Query(..., ge=1, le=5, description="火灾等级1-5")
):
    """
    接收火灾地点和等级，生成处置建议并写入数据库
    """
    try:
        # 1. 场景自动识别
        scene_keywords = {
            "普通居民区": ["小区", "社区", "居民楼", "单元"],
            "人员密集区": ["商场", "超市", "学校", "医院", "广场"],
            "易燃易爆区": ["加油站", "油库", "化工厂", "仓库"],
            "办公区": ["写字楼", "办公室", "产业园"]
        }
        scene = "普通居民区"
        for key, keywords in scene_keywords.items():
            if any(kw in location for kw in keywords):
                scene = key
                break
        
        # 2. 获取缓存的气象/交通数据
        weather_data = agent_cache.get("weather_data", {})
        traffic_data = agent_cache.get("traffic_data", {})
        
        # 格式化缓存数据
        weather_str = "; ".join([f"{k}：{v}" for k, v in weather_data.items()]) if weather_data else "无"
        traffic_str = "; ".join([f"{k}：{v}" for k, v in traffic_data.items()]) if traffic_data else "无"
        
        # 3. 基础处置建议
        basic_suggestion_map = {
            1: "派遣1辆消防车，现场核查是否为误报",
            2: "派遣2辆消防车+3名消防员，快速处置小型火灾",
            3: "派遣3辆消防车+5名消防员，封锁现场，疏散周边50米人员",
            4: "派遣5辆消防车+10名消防员，联动医疗、交警部门支援",
            5: "启动一级应急响应，派遣多支消防队伍，请求上级支援"
        }
        basic_suggestion = basic_suggestion_map.get(severity, "请根据实际情况调度")
        
        # 4. AI研判建议（模拟）
        ai_suggestion = f"""基于{scene}场景、{severity}级火灾及以下协同数据生成建议：
1. 气象条件：{weather_str}，需注意火势扩散风险；
2. 交通条件：{traffic_str}，建议按推荐路线派遣消防车；
3. 处置措施：{basic_suggestion}；
4. 联动建议：等级≥3时，建议联动医疗/安防智能体。"""
        
        # 5. 救援资源配置
        resource_config = {
            "fire_engine": min(severity + 1, 5),
            "firefighter": severity * 2 + 1,
            "need_medical": severity >= 3,
            "need_security": severity >= 4
        }
        
        # 6. 写入数据库
        event_id = None
        try:
            db_path = "fire_agent.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            alarm_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''
                INSERT INTO fire_events (location, alarm_time, severity, status, scene)
                VALUES (?, ?, ?, ?, ?)
            ''', (location, alarm_time, severity, "processing", scene))
            event_id = cursor.lastrowid
            conn.commit()
            conn.close()
            print(f"✅ 事件写入成功！event_id={event_id}，场景={scene}")
        except Exception as e:
            print(f"❌ 保存事件失败：{str(e)}")
            # 兜底生成临时ID
            event_id = hash(location + str(severity)) % 1000
        
        # 7. 返回结果
        return {
            "code": 200,
            "msg": "success",
            "data": {
                "event_id": event_id,
                "location": location,
                "severity": severity,
                "scene": scene,
                "scene_suggestion": f"{scene}处置要点：{basic_suggestion}",
                "basic_suggestion": basic_suggestion,
                "ai_suggestion": ai_suggestion,
                "resource_config": resource_config,
                "weather_data": weather_str,
                "traffic_data": traffic_str,
                "status": "processing",
                "process_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    except Exception as e:
        return {
            "code": 500,
            "msg": f"处理火灾事件失败：{str(e)}",
            "data": {}
        }

@router.get("/api/get_fire_events", summary="查询历史火灾事件")
def get_fire_events(status: str = Query(None, description="事件状态：pending/processing/completed")):
    """
    查询数据库中的火灾事件，支持按状态筛选
    """
    try:
        db_path = "fire_agent.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 构建查询语句
        if status:
            cursor.execute("SELECT * FROM fire_events WHERE status = ?", (status,))
        else:
            cursor.execute("SELECT * FROM fire_events")
        
        # 获取字段名
        columns = [desc[0] for desc in cursor.description]
        # 转换为字典列表
        events = []
        for row in cursor.fetchall():
            event = dict(zip(columns, row))
            events.append(event)
        
        conn.close()
        
        return {
            "code": 200,
            "msg": "success",
            "count": len(events),
            "data": events
        }
    except Exception as e:
        return {
            "code": 500,
            "msg": f"查询事件失败：{str(e)}",
            "count": 0,
            "data": []
        }
@router.put("/api/update_fire_status", summary="更新火灾事件状态（结束/暂停）")
def update_fire_status(
    event_id: int = Query(..., description="火灾事件ID"),
    new_status: str = Query(..., description="新状态：completed/暂停/pending")
):
    """
    手动更新事件状态（比如火灾处置完成后改为completed）
    支持的状态：pending(待处理)/processing(处理中)/completed(已完成)/暂停
    """
    try:
        db_path = "fire_agent.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 验证事件是否存在
        cursor.execute("SELECT id FROM fire_events WHERE id = ?", (event_id,))
        if not cursor.fetchone():
            conn.close()
            return {
                "code": 404,
                "msg": f"事件ID {event_id} 不存在",
                "data": {}
            }
        
        # 更新状态
        cursor.execute("UPDATE fire_events SET status = ? WHERE id = ?", (new_status, event_id))
        conn.commit()
        conn.close()
        
        # 返回更新后的事件信息
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM fire_events WHERE id = ?", (event_id,))
        columns = [desc[0] for desc in cursor.description]
        event = dict(zip(columns, cursor.fetchone()))
        conn.close()
        
        print(f"✅ 事件{event_id}状态已更新为：{new_status}")
        return {
            "code": 200,
            "msg": f"事件{event_id}状态更新成功",
            "data": event
        }
    except Exception as e:
        return {
            "code": 500,
            "msg": f"更新状态失败：{str(e)}",
            "data": {}
        }
@router.put("/api/batch_complete_events", summary="批量标记事件为已完成")
def batch_complete_events(severity_le: int = Query(3, description="等级≤该值的事件批量完成")):
    """
    批量更新低等级火灾事件为已完成（演示用）
    """
    try:
        db_path = "fire_agent.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 更新等级≤severity_le的processing事件
        cursor.execute("""
            UPDATE fire_events 
            SET status = 'completed' 
            WHERE status = 'processing' AND severity <= ?
        """, (severity_le,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return {
            "code": 200,
            "msg": f"成功将{affected}个事件标记为已完成",
            "data": {"affected_count": affected}
        }
    except Exception as e:
        return {
            "code": 500,
            "msg": f"批量更新失败：{str(e)}",
            "data": {}
        }

@router.get("/api/fire/judge", summary="火灾智能体AI研判（高级接口）")
def fire_judge(
    location: str = Query(..., description="火灾地点"),
    severity: int = Query(..., ge=1, le=5, description="火灾等级1-5"),
    weather: str = Query("", description="手动传入气象信息"),
    traffic: str = Query("", description="手动传入交通信息")
):
    """
    AI研判接口，支持手动传入气象/交通数据（优先级高于缓存）
    """
    try:
        # 1. 场景识别
        scene_keywords = {
            "普通居民区": ["小区", "社区", "居民楼"],
            "人员密集区": ["商场", "学校", "医院"],
            "易燃易爆区": ["加油站", "化工厂"],
            "办公区": ["写字楼", "产业园"]
        }
        scene = "普通居民区"
        for key, keywords in scene_keywords.items():
            if any(kw in location for kw in keywords):
                scene = key
                break
        
        # 2. 数据优先级：手动传入 > 缓存
        final_weather = weather if weather else "; ".join([f"{k}：{v}" for k, v in agent_cache.get("weather_data", {}).items()]) or "无"
        final_traffic = traffic if traffic else "; ".join([f"{k}：{v}" for k, v in agent_cache.get("traffic_data", {}).items()]) or "无"
        
        # 3. AI建议生成
        ai_suggestion = f"""【AI研判建议 - {scene}】
火灾等级：{severity}级 | 地点：{location}
气象条件：{final_weather}
交通条件：{final_traffic}
核心建议：
1. 灭火力量：派遣{severity + 1}辆消防车，{severity * 2 + 1}名消防员；
2. 联动建议：{severity >= 3 and '联动医疗智能体派遣救护车' or '无需医疗支援'}；
3. 注意事项：{scene == '易燃易爆区' and '严禁使用水灭火，优先使用干粉灭火器' or '常规灭火作业'}。"""
        
        # 4. 写入数据库（兜底）
        event_id = None
        try:
            db_path = "fire_agent.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            alarm_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''
                INSERT INTO fire_events (location, alarm_time, severity, status, scene)
                VALUES (?, ?, ?, ?, ?)
            ''', (location, alarm_time, severity, "processing", scene))
            event_id = cursor.lastrowid
            conn.commit()
            conn.close()
        except Exception as e:
            event_id = hash(location + str(severity)) % 1000
        
        return {
            "code": 200,
            "msg": "success",
            "data": {
                "event_id": event_id,
                "location": location,
                "severity": severity,
                "scene": scene,
                "weather_data": final_weather,
                "traffic_data": final_traffic,
                "ai_suggestion": ai_suggestion,
                "process_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    except Exception as e:
        return {
            "code": 500,
            "msg": f"AI研判失败：{str(e)}",
            "data": {}
        }

@router.get("/api/fire/status", summary="查询消防智能体状态")
def get_fire_agent_status():
    """
    查询智能体当前状态及缓存数据情况
    """
    return {
        "agent": "fire_agent",
        "status": "running",
        "has_weather_data": bool(agent_cache["weather_data"]),
        "has_traffic_data": bool(agent_cache["traffic_data"]),
        "has_medical_response": bool(agent_cache["medical_response"]),
        "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# ==================== 可视化接口 ====================
@router.get("/api/agent/real_time_status", summary="实时状态数据（大屏展示）")
def get_real_time_status():
    """
    获取大屏展示所需的实时数据：事件数、等级分布、场景分布等
    """
    try:
        # 查询数据库中的处理中事件
        db_path = "fire_agent.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT severity, scene FROM fire_events WHERE status = 'processing'")
        events = cursor.fetchall()
        conn.close()
        
        # 统计等级分布
        severity_dist = {1:0, 2:0, 3:0, 4:0, 5:0}
        for event in events:
            severity = event[0]
            if severity in severity_dist:
                severity_dist[severity] += 1
        
        # 统计场景分布
        scene_dist = {}
        for event in events:
            scene = event[1]
            scene_dist[scene] = scene_dist.get(scene, 0) + 1
        
        # 最新10条事件
        latest_events = []
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM fire_events ORDER BY id DESC LIMIT 10")
            columns = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                latest_events.append(dict(zip(columns, row)))
            conn.close()
        except:
            latest_events = []
        
        return {
            "code": 200,
            "data": {
                "agent_info": get_fire_agent_status(),
                "processing_count": len(events),
                "severity_distribution": severity_dist,
                "scene_distribution": scene_dist,
                "latest_10_events": latest_events
            }
        }
    except Exception as e:
        # 兜底：无数据库数据时返回模拟数据
        return {
            "code": 200,
            "data": {
                "agent_info": get_fire_agent_status(),
                "processing_count": 0,
                "severity_distribution": {1:0, 2:0, 3:0, 4:0, 5:0},
                "scene_distribution": {},
                "latest_10_events": []
            }
        }

@router.get("/api/agent/rescue_track", summary="模拟救援轨迹（大屏展示用）")
def get_rescue_track(event_id: int):
    """
    获取指定火灾事件的模拟救援轨迹
    :param event_id: 火灾事件ID
    :return: 救援轨迹经纬度+资源信息
    """
    try:
        # 纯模拟轨迹生成（无数据库依赖）
        base_lng = 120.123456  # 基础经度（杭州为例）
        base_lat = 30.256789   # 基础纬度
        
        # 计算时间：出发时间 + 每步递增10秒
        start_datetime = datetime.datetime.now()
        estimated_arrival_datetime = start_datetime + datetime.timedelta(minutes=8)  # 预计8分钟到达
        
        # 生成10个轨迹点（共8分钟=480秒，每步约48秒，简化为每步10秒）
        track = []
        for i in range(10):
            # 每个轨迹点的时间 = 出发时间 + i*10秒
            point_time = start_datetime + datetime.timedelta(seconds=i*10)
            # 经纬度递增（模拟行进）
            lng = round(base_lng + i * 0.001, 6)
            lat = round(base_lat + i * 0.001, 6)
            
            track.append({
                "lng": lng,
                "lat": lat,
                "time": point_time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "行进中" if i < 9 else "已到达"
            })
        
        # 模拟救援资源配置
        resource = {
            "fire_engine": 3,
            "firefighter": 5,
            "need_medical": True,
            "need_security": False
        }
        
        return {
            "code": 200,
            "data": {
                "event_id": event_id,
                "track": track,
                "resource": resource,
                "start_time": start_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                "estimated_arrival": estimated_arrival_datetime.strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    except Exception as e:
        # 终极兜底：即使报错也返回200
        print(f"⚠️ 生成救援轨迹警告：{str(e)}")
        # 兜底轨迹（时间也递增）
        start_datetime = datetime.datetime.now()
        track = []
        for i in range(1):
            point_time = start_datetime + datetime.timedelta(seconds=i*10)
            track.append({
                "lng": 120.123456,
                "lat": 30.256789,
                "time": point_time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "已到达"
            })
        return {
            "code": 200,
            "data": {
                "event_id": event_id,
                "track": track,
                "resource": {"fire_engine": 2, "firefighter": 4},
                "start_time": start_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                "estimated_arrival": start_datetime.strftime("%Y-%m-%d %H:%M:%S")
            }
        }
# 挂载路由
app.include_router(router)

# 启动服务
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app="mock_agents:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["."]
    )