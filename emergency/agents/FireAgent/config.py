# config.py - 所有配置统一管理
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ==================== 数据库配置 ====================
# 动态获取当前文件目录，避免硬编码路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "fire_agent.db")

# ==================== 大模型配置 ====================
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")  # 空值兜底
QWEN_MODEL = "qwen-turbo"
TEMPERATURE = 0.1

# ==================== 智能体通信配置 ====================
# 各智能体端口分配（统一约定）
AGENT_PORTS = {
    "fire_agent": 8000,          # 消防智能体（当前）
    "weather_agent": 8001,       # 气象智能体
    "traffic_agent": 8002,       # 交通智能体
    "medical_agent": 8003,       # 医疗智能体
    "security_agent": 8004       # 安防智能体
}
# 智能体通信基础URL模板
BASE_AGENT_URL = "http://127.0.0.1:{port}/api/agent/receive"

# ==================== 火灾等级配置 ====================
# 各等级救援资源配置（可扩展）
SEVERITY_CONFIG = {
    1: {"fire_engine": 1, "firefighter": 0, "need_medical": False, "need_security": False},
    2: {"fire_engine": 2, "firefighter": 2, "need_medical": False, "need_security": False},
    3: {"fire_engine": 3, "firefighter": 5, "need_medical": True, "need_security": False},
    4: {"fire_engine": 5, "firefighter": 10, "need_medical": True, "need_security": True},
    5: {"fire_engine": 10, "firefighter": 20, "need_medical": True, "need_security": True}
}

# ==================== 场景化配置 ====================
# 火灾场景关键词匹配（用于自动识别场景）
SCENE_KEYWORDS = {
    "人员密集区": ["商场", "学校", "医院", "广场", "地铁站", "车站", "市场"],
    "易燃易爆区": ["加油站", "化工厂", "仓库", "加气站", "油库", "危险品"],
    "普通居民区": ["小区", "楼栋", "单元", "住宅", "家属院"],
    "道路沿线": ["公路", "高速", "路口", "街道", "主干道"]
}

# 场景化处置建议
SCENE_SUGGESTION = {
    "人员密集区": "优先疏散人员，封锁出入口，联动安防智能体维持现场秩序，避免踩踏事故",
    "易燃易爆区": "立即封锁周边1公里范围，禁止明火/吸烟，联动气象智能体监测风向，防止爆炸扩散",
    "普通居民区": "优先排查燃气/电路隐患，通知物业配合救援，逐户确认人员撤离情况",
    "道路沿线": "联动交通智能体封锁相关车道，引导救援车辆优先通行，避免交通拥堵"
}

# ==================== 可视化配置 ====================
# 城市基础经纬度（以杭州为例，可根据需要修改）
CITY_BASE_LNG = 120.12
CITY_BASE_LAT = 30.25