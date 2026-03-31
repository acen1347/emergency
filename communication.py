"""
统一通信模块 - 所有智能体通过此模块进行消息传递和状态同步
"""
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field


@dataclass
class Message:
    """消息格式标准"""
    msg_id: str                    # 消息唯一ID
    sender: str                    # 发送者 (weather/fire/medical/traffic/security/coordinator)
    receiver: str                  # 接收者 (可指定 "all" 或具体智能体)
    msg_type: str                  # 消息类型 (command/status/query/response/event)
    content: Dict[str, Any]        # 消息内容
    timestamp: str                 # 时间戳
    priority: int = 1              # 优先级 1-3 (1最高)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


class CommunicationHub:
    """
    通信中心 - 单例模式，全局唯一
    所有智能体通过此中心收发消息、共享状态
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._message_queue: List[Message] = []           # 消息队列
        self._agent_status: Dict[str, Dict] = {}          # 各智能体状态
        self._global_state: Dict[str, Any] = {            # 全局共享状态
            "active_incident": None,      # 当前活跃事件
            "incident_type": None,        # 事件类型
            "incident_location": None,    # 事件位置
            "priority_level": None,       # 优先级
            "timestamp": None,            # 事件时间
        }
        self._subscribers: Dict[str, List[str]] = {}      # 订阅关系
    
    # ==================== 消息发送与接收 ====================
    
    def send(self, sender: str, receiver: str, msg_type: str, content: Dict, priority: int = 1) -> str:
        """发送消息，返回消息ID"""
        msg = Message(
            msg_id=str(uuid.uuid4()),
            sender=sender,
            receiver=receiver,
            msg_type=msg_type,
            content=content,
            timestamp=datetime.now().isoformat(),
            priority=priority
        )
        # 按优先级插入队列（优先级数字小的在前）
        inserted = False
        for i, existing_msg in enumerate(self._message_queue):
            if existing_msg.priority > msg.priority:
                self._message_queue.insert(i, msg)
                inserted = True
                break
        if not inserted:
            self._message_queue.append(msg)
        
        print(f"[通信] {sender} -> {receiver} [{msg_type}]: {content.get('summary', content)}")
        return msg.msg_id
    
    def receive(self, agent_name: str) -> List[Message]:
        """接收发给自己的消息"""
        messages = []
        remaining = []
        for msg in self._message_queue:
            if msg.receiver == agent_name or msg.receiver == "all":
                messages.append(msg)
            else:
                remaining.append(msg)
        self._message_queue = remaining
        return messages
    
    def broadcast(self, sender: str, msg_type: str, content: Dict, priority: int = 1):
        """广播消息给所有智能体"""
        self.send(sender, "all", msg_type, content, priority)
    
    # ==================== 状态管理 ====================
    
    def update_status(self, agent_name: str, status: Dict):
        """更新智能体状态"""
        self._agent_status[agent_name] = {
            **status,
            "last_update": datetime.now().isoformat()
        }
        print(f"[状态] {agent_name} 状态更新: {status.get('state', status)}")
    
    def get_agent_status(self, agent_name: str) -> Optional[Dict]:
        """获取指定智能体状态"""
        return self._agent_status.get(agent_name)
    
    def get_all_status(self) -> Dict:
        """获取所有智能体状态"""
        return self._agent_status.copy()
    
    def update_global_state(self, key: str, value: Any):
        """更新全局状态"""
        self._global_state[key] = value
        print(f"[全局] {key} = {value}")
    
    def get_global_state(self, key: str = None):
        """获取全局状态"""
        if key:
            return self._global_state.get(key)
        return self._global_state.copy()
    
    # ==================== 订阅机制 ====================
    
    def subscribe(self, agent_name: str, event_type: str):
        """订阅事件"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if agent_name not in self._subscribers[event_type]:
            self._subscribers[event_type].append(agent_name)
    
    def publish_event(self, event_type: str, event_data: Dict):
        """发布事件给所有订阅者"""
        for subscriber in self._subscribers.get(event_type, []):
            self.send("system", subscriber, "event", {
                "event_type": event_type,
                "data": event_data
            })
    
    # ==================== 系统信息 ====================
    
    def clear(self):
        """清空所有消息和状态（用于重置）"""
        self._message_queue.clear()
        self._agent_status.clear()
        self._global_state = {
            "active_incident": None, "incident_type": None,
            "incident_location": None, "priority_level": None, "timestamp": None
        }
    
    def get_queue_length(self) -> int:
        return len(self._message_queue)


# 全局单例实例
comm_hub = CommunicationHub()


# ==================== 智能体基类 ====================

class BaseAgent:
    """所有智能体的基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.comm = comm_hub
        self._running = True
        self._status = {"state": "idle", "message": "待命"}
        self._init_subscriptions()
    
    def _init_subscriptions(self):
        """子类重写此方法以订阅事件"""
        pass
    
    def update_status(self, state: str, message: str = "", **kwargs):
        """更新自身状态"""
        self._status = {"state": state, "message": message, **kwargs}
        self.comm.update_status(self.name, self._status)
    
    def send_to(self, receiver: str, msg_type: str, content: Dict, priority: int = 1):
        """发送消息给其他智能体"""
        return self.comm.send(self.name, receiver, msg_type, content, priority)
    
    def broadcast(self, msg_type: str, content: Dict, priority: int = 1):
        """广播消息"""
        self.comm.broadcast(self.name, msg_type, content, priority)
    
    def receive_messages(self) -> List[Message]:
        """接收发来的消息"""
        return self.comm.receive(self.name)
    
    def handle_message(self, msg: Message):
        """处理单条消息 - 子类重写"""
        pass
    
    def process_messages(self):
        """处理所有待处理消息"""
        messages = self.receive_messages()
        for msg in messages:
            self.handle_message(msg)
    
    def step(self):
        """每轮执行 - 子类重写"""
        self.process_messages()
    
    def get_status(self) -> Dict:
        return self._status