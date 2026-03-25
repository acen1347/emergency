# fire_agent.py - 火灾智能体核心逻辑（优化版，修复缩进错误）
import json
import sqlite3
import time
from datetime import datetime
import dashscope
from config import (
    DB_FILE, DASHSCOPE_API_KEY, QWEN_MODEL, TEMPERATURE,
    SEVERITY_CONFIG, SCENE_KEYWORDS, SCENE_SUGGESTION
)

class FireAgent:
    def __init__(self):
        self.agent_name = "fire_agent"
        self.status = "idle"
        # 新增：缓存其他智能体的协同数据
        self.weather_data = {}  # 气象智能体数据
        self.traffic_data = {}  # 交通智能体数据
        self.medical_response = {}  # 医疗智能体响应
        self.security_response = {}  # 安防智能体响应

    def judge_fire(self, location: str, severity: int, weather: str = "", traffic: str = ""):
        """
        核心功能：火情AI研判（融入多智能体协同+场景化）
        :param location: 火灾地点
        :param severity: 1-5级
        :param weather: 气象信息（手动传入/优先用缓存）
        :param traffic: 交通信息（手动传入/优先用缓存）
        :return: 标准化结果
        """
        self.status = "processing"
        
        # 1. 参数校验（严格校验）
        if not isinstance(severity, int) or not 1 <= severity <= 5:
            self.status = "error"
            return {"code": 400, "msg": "等级必须为1-5的整数", "data": None}
        if not location or not isinstance(location, str):
            self.status = "error"
            return {"code": 400, "msg": "地点不能为空且必须为字符串", "data": None}

        # 2. 场景自动识别（核心优化）
        scene = self._identify_scene(location)
        
        # 3. 优先使用缓存的协同数据（多智能体协同）
        weather = weather or self._get_cached_data("weather")
        traffic = traffic or self._get_cached_data("traffic")

        # 4. 通义千问生成AI建议（融入协同数据+场景）
        ai_suggestion = self._get_qwen_suggestion(location, severity, scene, weather, traffic)

        # 5. 写入数据库（带场景信息）
        from init_db import save_fire_event
        event_id = save_fire_event(location, severity, scene)

        # 6. 基础处置建议（基于等级）
        basic_suggestion_map = {
            1: "派遣1辆消防车，现场核查是否为误报",
            2: "派遣2辆消防车+2名消防员，快速处置小型火灾",
            3: "派遣3辆消防车+5名消防员，封锁现场，疏散周边50米人员",
            4: "派遣5辆消防车+10名消防员，联动医疗、交警部门支援",
            5: "启动一级应急响应，派遣多支消防队伍，请求上级支援"
        }

        # 7. 组装返回结果（包含场景+协同信息）
        self.status = "completed"
        return {
            "code": 200,
            "msg": "success",
            "data": {
                "event_id": event_id,
                "location": location,
                "severity": severity,
                "scene": scene,
                "scene_suggestion": SCENE_SUGGESTION[scene],
                "basic_suggestion": basic_suggestion_map[severity],
                "ai_suggestion": ai_suggestion,
                "resource_config": SEVERITY_CONFIG[severity],  # 救援资源配置
                "weather_data": weather,
                "traffic_data": traffic,
                "status": "processing",
                "process_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }

    def _identify_scene(self, location: str) -> str:
        """
        自动识别火灾场景
        :param location: 火灾地点
        :return: 场景名称（如人员密集区、易燃易爆区）
        """
        location_lower = location.lower()
        for scene, keywords in SCENE_KEYWORDS.items():
            if any(kw in location for kw in keywords):
                return scene
        return "普通居民区"  # 默认场景

    def _get_cached_data(self, data_type: str) -> str:
        """
        获取缓存的其他智能体数据
        :param data_type: weather/traffic/medical/security
        :return: 格式化的字符串
        """
        data_mapping = {
            "weather": self.weather_data,
            "traffic": self.traffic_data,
            "medical": self.medical_response,
            "security": self.security_response
        }
        data = data_mapping.get(data_type, {})
        if not data:
            return "无"
        
        # 格式化数据为易读字符串
        content = data.get("content", {})
        if isinstance(content, dict):
            return "; ".join([f"{k}：{v}" for k, v in content.items()])
        return str(content)

    def _get_qwen_suggestion(self, location, severity, scene, weather, traffic):
        """
        调用通义千问生成专业建议（融入场景+多智能体数据）
        """
        if not DASHSCOPE_API_KEY:
            return "⚠️ 未配置DASHSCOPE_API_KEY，请检查.env文件"
        
        # 构建精细化prompt（贴合应急调度场景）
        prompt = f"""
你是城市级应急调度系统的专业消防指挥智能体，需基于以下信息生成精准、可执行的火灾处置建议：

### 基础信息
- 火灾地点：{location}
- 火灾等级：{severity}级（1=轻微，5=重大）
- 火灾场景：{scene}

### 协同数据（来自其他智能体）
- 气象条件：{weather}
- 交通状况：{traffic}

### 输出要求
1. 分点说明，逻辑清晰（预警→调度→联动→善后）；
2. 必须结合场景特性（如人员密集区优先疏散）；
3. 明确需要联动的智能体（气象/交通/医疗/安防）及具体需求；
4. 建议符合城市应急调度规范，可落地执行；
5. 语言简洁，无多余格式，纯文本输出。
"""
        try:
            dashscope.api_key = DASHSCOPE_API_KEY
            resp = dashscope.Generation.call(
                model=QWEN_MODEL,
                prompt=prompt,
                temperature=TEMPERATURE,
                result_format="text"
            )
            if resp.status_code == 200:
                return resp.output.text.strip()
            else:
                return f"❌ API调用失败：{resp.message}"
        except Exception as e:
            return f"❌ 调用异常：{str(e)}"

    def _save_to_db(self, location, severity, scene="普通居民区"):
        """
        写入数据库（带重试机制，提升健壮性）
        """
        max_retry = 3  # 最大重试次数
        for retry in range(max_retry):
            try:
                conn = sqlite3.connect(DB_FILE)
                conn.execute("PRAGMA busy_timeout = 5000")  # 设置超时时间
                cursor = conn.cursor()
                local_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO fire_events (location, alarm_time, severity, status, scene)
                    VALUES (?, ?, ?, ?, ?)
                """, (location, local_time, severity, "processing", scene))
                event_id = cursor.lastrowid
                conn.commit()
                conn.close()
                return event_id
            except sqlite3.OperationalError as e:
                if retry < max_retry - 1:
                    time.sleep(1)  # 重试间隔1秒
                    continue
                print(f"❌ 写入数据库失败（重试{max_retry}次）：{e}")
                return None
            except Exception as e:
                print(f"❌ 写入数据库失败：{e}")
                return None

    def get_status(self):
        """获取智能体状态（包含协同数据状态）"""
        return {
            "agent": self.agent_name,
            "status": self.status,
            "has_weather_data": bool(self.weather_data),
            "has_traffic_data": bool(self.traffic_data),
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

# 测试：直接运行可验证功能
if __name__ == "__main__":
    agent = FireAgent()
    # 模拟缓存气象数据
    agent.weather_data = {"content": {"天气": "晴", "风向": "东北风2级", "温度": "25℃"}}
    # 模拟缓存交通数据
    agent.traffic_data = {"content": {"路况": "畅通", "救援路线": "主干道无拥堵"}}
    
    result = agent.judge_fire(
        location="杭州万象城商场",
        severity=3,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))