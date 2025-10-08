"""
TV直播源更新工具 - Python核心版
集成配置管理、核心功能
版本: 4.1.0 Python核心版
"""

import os
import sys
import configparser
import logging
import re
from typing import Any, Dict, List, Tuple, Optional
import datetime
import asyncio
import gzip
import pickle
import socket
import aiohttp
from urllib.parse import urljoin, urlparse
import pytz

# ==================== 常量定义 ====================
class Paths:
    """路径常量"""
    # 配置文件目录
    CONFIG_DIR = "config"
    # 输出文件目录  
    OUTPUT_DIR = "output"
    # 日志文件目录
    LOGS_DIR = "logs"
    
    # 配置文件路径
    CONFIG_FILE = os.path.join(CONFIG_DIR, "config.ini")                    # 主配置文件
    SUBSCRIBE_FILE = os.path.join(CONFIG_DIR, "subscribe.txt")             # 订阅源文件
    WHITELIST_FILE = os.path.join(CONFIG_DIR, "whitelist.txt")             # 白名单文件
    LOCAL_FILE = os.path.join(CONFIG_DIR, "local.txt")                     # 本地源文件
    SOURCE_FILE = os.path.join(CONFIG_DIR, "demo.txt")                     # 模板文件
    FINAL_FILE = os.path.join(OUTPUT_DIR, "result.txt")                    # 最终结果文件
    CACHE_FILE = os.path.join(OUTPUT_DIR, "cache.pkl.gz")                  # 缓存文件
    LOG_FILE = os.path.join(LOGS_DIR, "update.log")                        # 日志文件
    
    # 组播配置文件目录
    RTP_DIR = os.path.join(CONFIG_DIR, "rtp")

class DefaultConfig:
    """默认配置值 - 所有可配置参数的默认值"""
    
    # ========== 功能开关配置 ==========
    OPEN_DRIVER = False                            # 开启浏览器运行（较消耗性能）
    OPEN_EPG = False                               # 开启EPG功能（电子节目指南）
    OPEN_EMPTY_CATEGORY = False                    # 开启无结果频道分类
    OPEN_FILTER_RESOLUTION = True                  # 开启分辨率过滤
    OPEN_FILTER_SPEED = True                       # 开启速率过滤
    OPEN_HOTEL = False                             # 开启酒店源功能
    OPEN_HOTEL_FOODIE = True                       # 开启Foodie酒店源工作模式
    OPEN_HOTEL_FOFA = False                        # 开启FOFA酒店源工作模式
    OPEN_LOCAL = True                              # 开启本地源功能
    OPEN_M3U_RESULT = True                         # 开启生成M3U文件类型结果
    OPEN_MULTICAST = False                         # 开启组播源功能
    OPEN_MULTICAST_FOODIE = True                   # 开启Foodie组播源工作模式
    OPEN_MULTICAST_FOFA = False                    # 开启FOFA组播源工作模式
    OPEN_REQUEST = False                           # 开启查询请求（仅针对酒店源与组播源）
    OPEN_RTMP = True                               # 开启RTMP推流功能（需要安装FFmpeg）
    OPEN_SERVICE = True                            # 开启页面服务
    OPEN_SPEED_TEST = True                         # 开启测速功能
    OPEN_SUBSCRIBE = True                          # 开启订阅源功能
    OPEN_SUPPLY = True                             # 开启补偿机制模式
    OPEN_UPDATE = True                             # 开启更新功能
    OPEN_UPDATE_TIME = True                        # 开启显示更新时间
    OPEN_URL_INFO = False                          # 开启显示接口说明信息
    OPEN_USE_CACHE = True                          # 开启使用本地缓存数据
    OPEN_HISTORY = True                            # 开启使用历史更新结果
    OPEN_HEADERS = False                           # 开启使用M3U内含的请求头验证信息
    SPEED_TEST_FILTER_HOST = False                 # 测速阶段使用Host地址进行过滤
    IPV6_SUPPORT = False                           # 强制认为当前网络支持IPv6
    
    # ========== 网络服务配置 ==========
    APP_HOST = "http://localhost"                  # 页面服务Host地址
    APP_PORT = 8000                                # 页面服务端口
    CDN_URL = ""                                   # CDN代理加速地址
    
    # ========== 文件路径配置 ==========
    FINAL_FILE = "output/result.txt"               # 生成结果文件路径
    LOCAL_FILE = "config/local.txt"                # 本地源文件路径
    SOURCE_FILE = "config/demo.txt"                # 模板文件路径
    
    # ========== 数量限制配置 ==========
    HOTEL_NUM = 10                                 # 结果中偏好的酒店源接口数量
    HOTEL_PAGE_NUM = 1                             # 酒店地区获取分页数量
    MULTICAST_NUM = 10                             # 结果中偏好的组播源接口数量
    MULTICAST_PAGE_NUM = 1                         # 组播地区获取分页数量
    LOCAL_NUM = 10                                 # 结果中偏好的本地源接口数量
    SUBSCRIBE_NUM = 10                             # 结果中偏好的订阅源接口数量
    URLS_LIMIT = 10                                # 单个频道接口数量
    
    # ========== 地区设置配置 ==========
    HOTEL_REGION_LIST = "全部"                     # 酒店源地区列表，"全部"表示所有地区
    MULTICAST_REGION_LIST = "全部"                 # 组播源地区列表，"全部"表示所有地区
    
    # ========== 网络优化配置 ==========
    ISP = ""                                       # 接口运营商，支持关键字过滤
    IPV4_NUM = ""                                  # 结果中偏好的IPv4接口数量
    IPV6_NUM = ""                                  # 结果中偏好的IPv6接口数量
    IPV_TYPE = "全部"                              # 生成结果中接口的协议类型
    IPV_TYPE_PREFER = "auto"                       # 接口协议类型偏好
    LOCATION = ""                                  # 接口归属地，支持关键字过滤
    
    # ========== 质量设置配置 ==========
    MIN_RESOLUTION = "1920x1080"                   # 接口最小分辨率
    MAX_RESOLUTION = "1920x1080"                   # 接口最大分辨率
    MIN_SPEED = 0.5                                # 接口最小速率（单位M/s）
    
    # ========== 时间设置配置 ==========
    RECENT_DAYS = 30                               # 获取最近时间范围内更新的接口（单位天）
    REQUEST_TIMEOUT = 10                           # 查询请求超时时长（单位秒）
    SPEED_TEST_LIMIT = 10                          # 同时执行测速的接口数量
    SPEED_TEST_TIMEOUT = 10                        # 单个接口测速超时时长（单位秒）
    TIME_ZONE = "Asia/Shanghai"                    # 时区设置
    UPDATE_INTERVAL = 12                           # 定时执行更新时间间隔（单位小时）
    UPDATE_TIME_POSITION = "top"                   # 更新时间显示位置

# 地区映射配置 - 中文地区名到英文标识的映射
REGION_MAP = {
    "北京": "beijing", "上海": "shanghai", "广州": "guangzhou", "深圳": "shenzhen",
    "杭州": "hangzhou", "成都": "chengdu", "武汉": "wuhan", "西安": "xian",
    "南京": "nanjing", "重庆": "chongqing", "天津": "tianjin", "苏州": "suzhou",
    "长沙": "changsha", "郑州": "zhengzhou", "沈阳": "shenyang", "青岛": "qingdao",
    "宁波": "ningbo", "东莞": "dongguan", "无锡": "wuxi", "厦门": "xiamen",
    "合肥": "hefei", "福州": "fuzhou", "济南": "jinan", "大连": "dalian"
}

# 支持的视频格式列表
SUPPORTED_FORMATS = {'.m3u8', '.mp4', '.flv', '.ts', '.mkv', '.avi'}

# 用户代理字符串
USER_AGENT = "Mozilla/5.0 (compatible; TVSourceUpdater/4.1.0)"

# ==================== 工具函数 ====================
class Utility:
    """工具函数集合"""
    
    @staticmethod
    def ensure_directories():
        """
        确保必要的目录存在
        自动创建config、output、logs等必要目录
        """
        directories = [
            Paths.CONFIG_DIR,    # 配置文件目录
            Paths.OUTPUT_DIR,    # 输出文件目录  
            Paths.LOGS_DIR,      # 日志文件目录
            Paths.RTP_DIR        # 组播配置目录
        ]
        for directory in directories:
            if directory and not os.path.exists(directory):
                try:
                    os.makedirs(directory, exist_ok=True)
                    logging.info(f"创建目录: {directory}")
                except Exception as e:
                    logging.error(f"创建目录失败 {directory}: {e}")
    
    @staticmethod
    def setup_logging():
        """
        设置日志配置
        配置日志级别、格式和输出位置
        """
        Utility.ensure_directories()
        try:
            logging.basicConfig(
                level=logging.INFO,  # 日志级别：INFO
                format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',  # 日志格式
                handlers=[
                    logging.FileHandler(Paths.LOG_FILE, encoding='utf-8'),  # 文件处理器
                    logging.StreamHandler(sys.stdout)  # 控制台处理器
                ]
            )
            logging.info("日志系统初始化完成")
        except Exception as e:
            print(f"日志初始化失败: {e}")
    
    @staticmethod
    def resource_path(relative_path: str) -> str:
        """
        获取资源文件的绝对路径
        
        Args:
            relative_path: 相对路径
            
        Returns:
            绝对路径
        """
        try:
            base_path = os.path.dirname(os.path.abspath(__file__))
            return os.path.join(base_path, relative_path)
        except Exception:
            return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        验证URL格式是否有效
        
        Args:
            url: 要验证的URL字符串
            
        Returns:
            bool: URL是否有效
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def format_interval(seconds: float) -> str:
        """
        格式化时间间隔为可读字符串
        
        Args:
            seconds: 时间间隔（秒）
            
        Returns:
            格式化后的时间字符串
        """
        if seconds < 60:
            return f"{int(seconds)}秒"
        elif seconds < 3600:
            return f"{int(seconds // 60)}分{int(seconds % 60)}秒"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{int(hours)}时{int(minutes)}分"
    
    @staticmethod
    def get_ip_address() -> str:
        """
        获取本机IP地址
        
        Returns:
            IP地址字符串
        """
        try:
            # 获取本地IP
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            return f"http://{local_ip}:{get_config().app_port}"
        except Exception as e:
            logging.warning(f"获取IP地址失败: {e}")
            return "http://localhost:8000"
    
    @staticmethod
    def check_ipv6_support() -> bool:
        """
        检查IPv6支持
        
        Returns:
            bool: 是否支持IPv6
        """
        try:
            if not socket.has_ipv6:
                return False
            
            # 尝试创建IPv6 socket
            with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)
                try:
                    sock.connect(('ipv6.google.com', 80))
                    return True
                except:
                    return False
        except Exception as e:
            logging.warning(f"检查IPv6支持时出错: {e}")
            return False

    @staticmethod
    def read_file_content(file_path: str) -> str:
        """
        读取文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容字符串
        """
        try:
            if not os.path.exists(file_path):
                return ""
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logging.error(f"读取文件失败 {file_path}: {e}")
            return ""

    @staticmethod
    def write_file_content(file_path: str, content: str) -> bool:
        """
        写入文件内容
        
        Args:
            file_path: 文件路径
            content: 要写入的内容
            
        Returns:
            bool: 是否成功
        """
        try:
            Utility.ensure_directories()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logging.info(f"文件写入成功: {file_path}")
            return True
        except Exception as e:
            logging.error(f"写入文件失败 {file_path}: {e}")
            return False

    @staticmethod
    def get_file_stats(file_path: str) -> Dict[str, Any]:
        """
        获取文件统计信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件统计信息字典
        """
        try:
            if not os.path.exists(file_path):
                return {"exists": False}
            
            stat = os.stat(file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                channel_count = sum(1 for line in lines if line.strip() and not line.startswith('#') and ',' in line)
            
            return {
                "exists": True,
                "size": stat.st_size,
                "modified": datetime.datetime.fromtimestamp(stat.st_mtime),
                "channel_count": channel_count,
                "line_count": len(lines)
            }
        except Exception as e:
            logging.error(f"获取文件统计失败 {file_path}: {e}")
            return {"exists": False, "error": str(e)}

# ==================== 配置管理器 ====================
class ConfigValidator:
    """配置验证器 - 验证配置文件的有效性"""
    
    @staticmethod
    def validate_all(config_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证所有配置项的有效性
        
        Args:
            config_dict: 配置字典
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误/警告信息列表)
        """
        errors = []    # 错误信息列表
        warnings = []  # 警告信息列表
        
        try:
            # 验证必需配置项
            ConfigValidator._validate_required_settings(config_dict, errors)
            # 验证布尔类型配置
            ConfigValidator._validate_boolean_settings(config_dict, warnings)
            # 验证数值类型配置
            ConfigValidator._validate_numeric_settings(config_dict, warnings)
            # 验证文件存在性
            ConfigValidator._validate_file_existence(config_dict, warnings)
            
            return len(errors) == 0, errors + warnings
            
        except Exception as e:
            logging.error(f"配置验证过程出错: {e}")
            return False, [f"配置验证失败: {e}"]
    
    @staticmethod
    def _validate_required_settings(config_dict: Dict[str, Any], errors: List[str]):
        """
        验证必需配置项是否存在
        
        Args:
            config_dict: 配置字典
            errors: 错误信息列表
        """
        required_settings = [
            'open_update',         # 开启更新功能
            'open_speed_test',     # 开启测速功能  
            'open_service',        # 开启页面服务
            'speed_test_limit',    # 测速并发数量
            'speed_test_timeout',  # 测速超时时间
            'update_interval'      # 更新间隔时间
        ]
        
        for setting in required_settings:
            if setting not in config_dict:
                errors.append(f"缺少必需配置项: {setting}")
    
    @staticmethod
    def _validate_boolean_settings(config_dict: Dict[str, Any], warnings: List[str]):
        """
        验证布尔类型配置项的值类型
        
        Args:
            config_dict: 配置字典
            warnings: 警告信息列表
        """
        boolean_settings = [
            'open_driver', 'open_epg', 'open_empty_category', 'open_filter_resolution',
            'open_filter_speed', 'open_hotel', 'open_hotel_foodie', 'open_hotel_fofa',
            'open_local', 'open_m3u_result', 'open_multicast', 'open_multicast_foodie',
            'open_multicast_fofa', 'open_request', 'open_rtmp', 'open_service', 
            'open_speed_test', 'open_subscribe', 'open_supply', 'open_update', 
            'open_update_time', 'open_url_info', 'open_use_cache', 'open_history', 
            'open_headers', 'speed_test_filter_host', 'ipv6_support'
        ]
        
        for setting in boolean_settings:
            if setting in config_dict:
                value = config_dict[setting]
                if not isinstance(value, bool):
                    warnings.append(f"配置项 {setting} 应为布尔值，当前值: {value}")
    
    @staticmethod
    def _validate_numeric_settings(config_dict: Dict[str, Any], warnings: List[str]):
        """
        验证数值类型配置项的范围
        
        Args:
            config_dict: 配置字典
            warnings: 警告信息列表
        """
        numeric_settings = {
            'app_port': (1, 65535),           # 端口号范围
            'hotel_num': (0, 1000),           # 酒店源数量范围
            'hotel_page_num': (1, 100),       # 酒店页数范围
            'multicast_num': (0, 1000),       # 组播源数量范围
            'multicast_page_num': (1, 100),   # 组播页数范围
            'local_num': (0, 1000),           # 本地源数量范围
            'subscribe_num': (0, 1000),       # 订阅源数量范围
            'urls_limit': (1, 100),           # URL限制范围
            'speed_test_limit': (1, 100),     # 测速并发范围
            'speed_test_timeout': (1, 60),    # 测速超时范围
            'request_timeout': (1, 60),       # 请求超时范围
            'update_interval': (0, 24*7),     # 更新间隔范围
            'recent_days': (1, 365)           # 最近天数范围
        }
        
        for setting, (min_val, max_val) in numeric_settings.items():
            if setting in config_dict:
                value = config_dict[setting]
                if value is not None and not (min_val <= value <= max_val):
                    warnings.append(f"配置项 {setting} 值 {value} 超出建议范围 ({min_val}-{max_val})")
    
    @staticmethod
    def _validate_file_existence(config_dict: Dict[str, Any], warnings: List[str]):
        """
        验证相关文件是否存在
        
        Args:
            config_dict: 配置字典
            warnings: 警告信息列表
        """
        # 检查源文件是否存在
        if config_dict.get('open_update') and not os.path.exists(config_dict.get('source_file', '')):
            warnings.append(f"源文件不存在: {config_dict.get('source_file')}")
        
        # 检查本地源文件是否存在
        if config_dict.get('open_local') and not os.path.exists(config_dict.get('local_file', '')):
            warnings.append(f"本地源文件不存在: {config_dict.get('local_file')}")
        
        # 检查订阅文件是否存在
        if config_dict.get('open_subscribe') and not os.path.exists(Paths.SUBSCRIBE_FILE):
            warnings.append(f"订阅文件不存在: {Paths.SUBSCRIBE_FILE}")

class EnhancedConfig:
    """增强配置类 - 提供类型安全的配置访问"""
    
    def __init__(self, config_parser: configparser.ConfigParser = None):
        """
        初始化配置
        
        Args:
            config_parser: 配置解析器对象
        """
        self._config = config_parser
        self._setup_defaults()  # 设置默认值
    
    def _setup_defaults(self):
        """设置所有配置项的默认值"""
        for key in dir(DefaultConfig):
            if not key.startswith('_'):  # 排除私有属性
                value = getattr(DefaultConfig, key)
                setattr(self, key.lower(), value)  # 转换为小写属性名
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键名
            default: 默认值
            
        Returns:
            配置值
        """
        try:
            # 首先检查实例属性
            if hasattr(self, key):
                return getattr(self, key)
                
            # 然后检查配置文件
            if self._config and self._config.has_option('Settings', key):
                value = self._config.get('Settings', key)
                return self._convert_value(key, value)
            else:
                # 最后使用默认配置
                default_key = key.upper()
                if hasattr(DefaultConfig, default_key):
                    return getattr(DefaultConfig, default_key)
                return default
        except Exception as e:
            logging.warning(f"获取配置 {key} 时出错: {e}, 使用默认值: {default}")
            return default
    
    def _convert_value(self, key: str, value: str) -> Any:
        """
        转换配置值类型
        
        Args:
            key: 配置键名
            value: 原始字符串值
            
        Returns:
            转换后的值
        """
        if value.strip() == '':  # 空字符串处理
            default_key = key.upper()
            if hasattr(DefaultConfig, default_key):
                return getattr(DefaultConfig, default_key)
            return ''
            
        # 布尔值转换
        if key.startswith('open_') or key in ['ipv6_support', 'speed_test_filter_host']:
            return value.lower() in ('true', 'yes', '1', 'on')
        
        # 整数转换
        int_keys = ['app_port', 'hotel_num', 'hotel_page_num', 'multicast_num', 
                   'multicast_page_num', 'local_num', 'subscribe_num', 'urls_limit', 
                   'speed_test_limit', 'speed_test_timeout', 'request_timeout', 
                   'update_interval', 'recent_days']
        if key in int_keys:
            try:
                return int(value)
            except ValueError:
                logging.warning(f"配置 {key} 的值 {value} 不是有效整数，使用默认值")
                default_key = key.upper()
                return getattr(DefaultConfig, default_key, 0)
        
        # 浮点数转换
        if key == 'min_speed':
            try:
                return float(value)
            except ValueError:
                logging.warning(f"配置 {key} 的值 {value} 不是有效浮点数，使用默认值")
                return DefaultConfig.MIN_SPEED
        
        # 列表转换（用于地区列表）
        if key in ['hotel_region_list', 'multicast_region_list']:
            if value == '全部':
                return ['全部']
            return [item.strip() for item in value.split(',') if item.strip()]
        
        # 字符串值直接返回
        return value
    
    def __getattr__(self, name: str) -> Any:
        """
        属性访问代理
        
        Args:
            name: 属性名
            
        Returns:
            属性值
        """
        return self.get(name)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            配置字典
        """
        config_dict = {}
        for key in dir(DefaultConfig):
            if not key.startswith('_'):  # 排除私有属性
                config_key = key.lower()  # 转换为小写键名
                config_dict[config_key] = self.get(config_key)
        return config_dict
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        验证配置有效性
        
        Returns:
            Tuple[bool, List[str]]: (是否有效, 验证信息列表)
        """
        return ConfigValidator.validate_all(self.to_dict())

class ConfigManager:
    """配置管理器单例 - 管理配置的加载和保存"""
    
    _instance = None  # 单例实例
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化配置管理器"""
        if not hasattr(self, '_initialized'):
            self._config = None           # 配置解析器
            self._enhanced_config = None  # 增强配置对象
            self._initialized = True
    
    def ensure_directories(self):
        """确保必要的目录存在"""
        Utility.ensure_directories()
    
    def load_config(self, config_path: str = Paths.CONFIG_FILE) -> bool:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            bool: 是否加载成功
        """
        try:
            self.ensure_directories()  # 确保目录存在
            
            # 如果配置文件不存在，使用默认配置
            if not os.path.exists(config_path):
                logging.warning(f"配置文件不存在: {config_path}，使用默认配置")
                self._enhanced_config = EnhancedConfig()
                return True
            
            # 读取配置文件
            parser = configparser.ConfigParser()
            parser.read(config_path, encoding='utf-8')
            
            self._config = parser
            self._enhanced_config = EnhancedConfig(parser)
            
            # 验证配置
            is_valid, messages = self._enhanced_config.validate()
            
            # 输出验证信息
            for message in messages:
                if "错误" in message:
                    logging.error(f"❌ {message}")
                else:
                    logging.warning(f"⚠️ {message}")
            
            if not is_valid:
                logging.error("❌ 配置验证失败")
                return False
                
            logging.info("✅ 配置文件加载成功")
            return True
            
        except Exception as e:
            logging.error(f"❌ 加载配置文件失败: {e}")
            return False
    
    def save_config(self, config_path: str = Paths.CONFIG_FILE) -> bool:
        """
        保存配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            bool: 是否保存成功
        """
        try:
            if not self._enhanced_config:
                logging.error("没有配置可保存")
                return False
            
            self.ensure_directories()  # 确保目录存在
            
            # 创建配置解析器
            if not self._config:
                self._config = configparser.ConfigParser()
                self._config.add_section('Settings')
            
            # 将当前配置值写入配置文件
            config_dict = self._enhanced_config.to_dict()
            for key, value in config_dict.items():
                if isinstance(value, bool):
                    self._config.set('Settings', key, str(value).lower())
                elif isinstance(value, list):
                    self._config.set('Settings', key, ','.join(value))
                else:
                    self._config.set('Settings', key, str(value))
            
            # 写入文件
            with open(config_path, 'w', encoding='utf-8') as f:
                self._config.write(f)
            
            logging.info(f"✅ 配置文件已保存: {config_path}")
            return True
            
        except Exception as e:
            logging.error(f"❌ 保存配置文件失败: {e}")
            return False
    
    @property
    def config(self) -> EnhancedConfig:
        """
        获取配置对象
        
        Returns:
            EnhancedConfig: 配置对象
        """
        if self._enhanced_config is None:
            self._enhanced_config = EnhancedConfig()  # 使用默认配置
        return self._enhanced_config

# 全局配置实例
config_manager = ConfigManager()

def load_config(config_path: str = Paths.CONFIG_FILE) -> bool:
    """
    加载配置的便捷函数
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        bool: 是否加载成功
    """
    return config_manager.load_config(config_path)

def save_config(config_path: str = Paths.CONFIG_FILE) -> bool:
    """
    保存配置的便捷函数
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        bool: 是否保存成功
    """
    return config_manager.save_config(config_path)

def get_config() -> EnhancedConfig:
    """
    获取配置对象的便捷函数
    
    Returns:
        EnhancedConfig: 配置对象
    """
    return config_manager.config

# ==================== 核心功能类 ====================
class TVSourceUpdater:
    """TV直播源更新器核心类"""
    
    def __init__(self):
        """初始化更新器"""
        self.config = get_config()
        self.session = None
        self.cache_data = {}
        self.stats = {
            "total_channels": 0,
            "total_urls": 0,
            "valid_urls": 0,
            "start_time": None,
            "end_time": None
        }
        
    async def initialize(self):
        """初始化异步会话"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={'User-Agent': USER_AGENT},
                timeout=aiohttp.ClientTimeout(total=self.config.request_timeout)
            )
        
        # 加载缓存数据
        if self.config.open_use_cache and os.path.exists(Paths.CACHE_FILE):
            await self.load_cache()
        
        self.stats["start_time"] = datetime.datetime.now()
    
    async def close(self):
        """关闭异步会话"""
        if self.session:
            await self.session.close()
            self.session = None
        
        self.stats["end_time"] = datetime.datetime.now()
    
    async def load_cache(self):
        """加载缓存数据"""
        try:
            with gzip.open(Paths.CACHE_FILE, 'rb') as f:
                self.cache_data = pickle.load(f)
            logging.info("✅ 缓存数据加载成功")
        except Exception as e:
            logging.warning(f"加载缓存失败: {e}")
            self.cache_data = {}
    
    async def save_cache(self):
        """保存缓存数据"""
        try:
            with gzip.open(Paths.CACHE_FILE, 'wb') as f:
                pickle.dump(self.cache_data, f)
            logging.info("✅ 缓存数据保存成功")
        except Exception as e:
            logging.error(f"保存缓存失败: {e}")
    
    async def update_sources(self):
        """
        更新直播源
        
        Returns:
            bool: 是否成功
        """
        try:
            logging.info("🚀 开始更新直播源...")
            
            # 收集所有源
            all_sources = await self.collect_all_sources()
            self.stats["total_channels"] = len(all_sources)
            self.stats["total_urls"] = sum(len(urls) for urls in all_sources.values())
            
            # 过滤和排序
            filtered_sources = await self.filter_sources(all_sources)
            self.stats["valid_urls"] = sum(len(urls) for urls in filtered_sources.values())
            
            # 生成结果文件
            result = await self.generate_result(filtered_sources)
            
            # 保存结果
            success = Utility.write_file_content(Paths.FINAL_FILE, result)
            
            if success:
                await self._log_statistics()
                # 保存缓存
                if self.config.open_use_cache:
                    await self.save_cache()
            else:
                logging.error("❌ 保存结果文件失败")
                
            return success
            
        except Exception as e:
            logging.error(f"❌ 更新直播源失败: {e}")
            return False
    
    async def _log_statistics(self):
        """记录统计信息"""
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        logging.info("📊 更新统计信息:")
        logging.info(f"   总频道数: {self.stats['total_channels']}")
        logging.info(f"   总URL数: {self.stats['total_urls']}")
        logging.info(f"   有效URL数: {self.stats['valid_urls']}")
        logging.info(f"   有效率: {self.stats['valid_urls']/self.stats['total_urls']*100:.1f}%" if self.stats['total_urls'] > 0 else "   有效率: 0%")
        logging.info(f"   耗时: {Utility.format_interval(duration)}")
    
    async def collect_all_sources(self) -> Dict[str, List[str]]:
        """
        收集所有来源的直播源
        
        Returns:
            频道到URL列表的映射
        """
        sources = {}
        
        # 本地源
        if self.config.open_local:
            local_sources = await self.load_local_sources()
            sources.update(local_sources)
            logging.info(f"📁 本地源: {len(local_sources)} 个频道")
        
        # 订阅源
        if self.config.open_subscribe:
            subscribe_sources = await self.load_subscribe_sources()
            sources.update(subscribe_sources)
            logging.info(f"📡 订阅源: {len(subscribe_sources)} 个频道")
        
        # 模板源
        if self.config.open_update and os.path.exists(Paths.SOURCE_FILE):
            template_sources = await self.load_template_sources()
            sources.update(template_sources)
            logging.info(f"📋 模板源: {len(template_sources)} 个频道")
        
        logging.info(f"📊 总计收集: {len(sources)} 个频道")
        return sources
    
    async def load_local_sources(self) -> Dict[str, List[str]]:
        """
        加载本地源文件
        
        Returns:
            本地源字典
        """
        return await self._load_text_sources(Paths.LOCAL_FILE)
    
    async def load_template_sources(self) -> Dict[str, List[str]]:
        """
        加载模板源文件
        
        Returns:
            模板源字典
        """
        return await self._load_text_sources(Paths.SOURCE_FILE)
    
    async def _load_text_sources(self, file_path: str) -> Dict[str, List[str]]:
        """
        加载文本格式的源文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            源字典
        """
        sources = {}
        content = Utility.read_file_content(file_path)
        
        if not content:
            logging.warning(f"文件为空或不存在: {file_path}")
            return sources
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if ',' in line:
                parts = line.split(',')
                if len(parts) >= 2:
                    channel = parts[0].strip()
                    url = parts[1].strip()
                    
                    if channel and url and Utility.is_valid_url(url):
                        if channel not in sources:
                            sources[channel] = []
                        sources[channel].append(url)
                else:
                    logging.warning(f"文件 {file_path} 第 {line_num} 行格式错误: {line}")
            else:
                logging.warning(f"文件 {file_path} 第 {line_num} 行缺少逗号分隔符: {line}")
        
        return sources
    
    async def load_subscribe_sources(self) -> Dict[str, List[str]]:
        """
        加载订阅源
        
        Returns:
            订阅源字典
        """
        sources = {}
        
        if not os.path.exists(Paths.SUBSCRIBE_FILE):
            logging.warning("订阅文件不存在")
            return sources
        
        content = Utility.read_file_content(Paths.SUBSCRIBE_FILE)
        subscribe_urls = [line.strip() for line in content.split('\n') 
                         if line.strip() and not line.startswith('#')]
        
        if not subscribe_urls:
            logging.warning("订阅文件为空")
            return sources
        
        # 并发获取所有订阅源
        tasks = []
        for url in subscribe_urls:
            if Utility.is_valid_url(url):
                tasks.append(self.fetch_subscribe_content(url))
            else:
                logging.warning(f"无效的订阅URL: {url}")
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logging.error(f"获取订阅源失败: {subscribe_urls[i]}, 错误: {result}")
                elif isinstance(result, dict):
                    sources.update(result)
        
        return sources
    
    async def fetch_subscribe_content(self, url: str) -> Dict[str, List[str]]:
        """
        获取订阅内容
        
        Args:
            url: 订阅URL
            
        Returns:
            订阅源字典
        """
        sources = {}
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # 根据URL后缀判断格式
                    if url.endswith('.m3u') or url.endswith('.m3u8'):
                        sources = self.parse_m3u_content(content)
                    else:
                        # 尝试解析其他格式
                        sources = self.parse_text_content(content)
                    
                    logging.info(f"✅ 获取订阅成功: {url}, 频道数: {len(sources)}")
                else:
                    logging.error(f"订阅请求失败: {url}, 状态码: {response.status}")
                    
        except asyncio.TimeoutError:
            logging.error(f"订阅请求超时: {url}")
        except Exception as e:
            logging.error(f"获取订阅内容失败 {url}: {e}")
        
        return sources
    
    def parse_m3u_content(self, content: str) -> Dict[str, List[str]]:
        """
        解析M3U格式内容
        
        Args:
            content: M3U内容
            
        Returns:
            解析后的源字典
        """
        sources = {}
        lines = content.split('\n')
        current_channel = None
        current_url = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('#EXTINF:'):
                # 提取频道名称
                match = re.search(r',(.+)$', line)
                if match:
                    current_channel = match.group(1).strip()
            elif line and not line.startswith('#') and current_channel:
                current_url = line
                if current_channel and current_url and Utility.is_valid_url(current_url):
                    if current_channel not in sources:
                        sources[current_channel] = []
                    sources[current_channel].append(current_url)
                current_channel = None
                current_url = None
        
        return sources
    
    def parse_text_content(self, content: str) -> Dict[str, List[str]]:
        """
        解析文本格式内容
        
        Args:
            content: 文本内容
            
        Returns:
            解析后的源字典
        """
        sources = {}
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if line and not line.startswith('#'):
                if ',' in line:
                    parts = line.split(',')
                    if len(parts) >= 2:
                        channel = parts[0].strip()
                        url = parts[1].strip()
                        
                        if channel and url and Utility.is_valid_url(url):
                            if channel not in sources:
                                sources[channel] = []
                            sources[channel].append(url)
                    else:
                        logging.warning(f"文本内容第 {line_num} 行格式错误: {line}")
                else:
                    logging.warning(f"文本内容第 {line_num} 行缺少逗号分隔符: {line}")
        
        return sources
    
    async def filter_sources(self, sources: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        过滤直播源
        
        Args:
            sources: 原始源字典
            
        Returns:
            过滤后的源字典
        """
        filtered_sources = {}
        
        for channel, urls in sources.items():
            valid_urls = []
            
            # 限制每个频道的URL数量
            limited_urls = urls[:self.config.urls_limit]
            
            # 并发检查URL有效性
            tasks = [self.is_valid_source(url) for url in limited_urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for url, is_valid in zip(limited_urls, results):
                if isinstance(is_valid, bool) and is_valid:
                    valid_urls.append(url)
                elif isinstance(is_valid, Exception):
                    logging.debug(f"URL检查失败 {url}: {is_valid}")
            
            if valid_urls:
                filtered_sources[channel] = valid_urls
        
        logging.info(f"🔍 源过滤完成: {len(filtered_sources)}/{len(sources)} 个频道")
        return filtered_sources
    
    async def is_valid_source(self, url: str) -> bool:
        """
        检查源是否有效
        
        Args:
            url: 源URL
            
        Returns:
            bool: 是否有效
        """
        try:
            async with self.session.head(url, allow_redirects=True, timeout=self.config.request_timeout) as response:
                return response.status == 200
        except asyncio.TimeoutError:
            logging.debug(f"URL检查超时: {url}")
            return False
        except Exception as e:
            logging.debug(f"URL检查失败: {url}, 错误: {e}")
            return False
    
    async def generate_result(self, sources: Dict[str, List[str]]) -> str:
        """
        生成结果内容
        
        Args:
            sources: 源字典
            
        Returns:
            结果内容字符串
        """
        lines = []
        
        # 添加文件头
        if self.config.open_update_time:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"# 直播源更新结果")
            lines.append(f"# 更新时间: {current_time}")
            lines.append(f"# 频道数量: {len(sources)}")
            lines.append(f"# 总URL数: {sum(len(urls) for urls in sources.values())}")
            lines.append("")
        
        # 添加频道数据
        for channel, urls in sorted(sources.items()):
            for url in urls:
                lines.append(f"{channel},{url}")
        
        return '\n'.join(lines)

# ==================== 命令行界面 ====================
class CommandLineInterface:
    """命令行界面"""
    
    @staticmethod
    def show_banner():
        """显示程序横幅"""
        print("=" * 60)
        print("📺 TV直播源更新工具 - Python核心版")
        print("版本: 4.1.0")
        print("=" * 60)
    
    @staticmethod
    def show_usage():
        """显示使用说明"""
        print("使用方法:")
        print("  python tv_updater.py                 # 正常更新模式")
        print("  python tv_updater.py --config        # 显示配置信息")
        print("  python tv_updater.py --stats         # 显示文件统计")
        print("  python tv_updater.py --help          # 显示帮助信息")
    
    @staticmethod
    def show_config_info():
        """显示配置信息"""
        config = get_config()
        config_dict = config.to_dict()
        
        print("\n📋 配置信息:")
        print("-" * 40)
        for key, value in sorted(config_dict.items()):
            if isinstance(value, bool):
                status = "✅ 开启" if value else "❌ 关闭"
                print(f"{key:25} : {status}")
            elif isinstance(value, list):
                print(f"{key:25} : {', '.join(value)}")
            else:
                print(f"{key:25} : {value}")
    
    @staticmethod
    def show_file_stats():
        """显示文件统计信息"""
        files_to_check = [
            (Paths.CONFIG_FILE, "主配置文件"),
            (Paths.LOCAL_FILE, "本地源文件"),
            (Paths.SUBSCRIBE_FILE, "订阅文件"),
            (Paths.SOURCE_FILE, "模板文件"),
            (Paths.FINAL_FILE, "结果文件"),
            (Paths.CACHE_FILE, "缓存文件")
        ]
        
        print("\n📊 文件统计信息:")
        print("-" * 50)
        for file_path, description in files_to_check:
            stats = Utility.get_file_stats(file_path)
            if stats["exists"]:
                if "channel_count" in stats:
                    print(f"{description:15} : ✅ 存在 (频道: {stats['channel_count']}, 大小: {stats['size']} bytes)")
                else:
                    print(f"{description:15} : ✅ 存在 (大小: {stats['size']} bytes)")
            else:
                print(f"{description:15} : ❌ 不存在")

# ==================== 主程序入口 ====================
async def main():
    """主程序入口 - Python核心版"""
    try:
        # 设置日志系统
        Utility.setup_logging()
        
        # 显示横幅
        CommandLineInterface.show_banner()
        
        # 处理命令行参数
        if len(sys.argv) > 1:
            if sys.argv[1] == '--help' or sys.argv[1] == '-h':
                CommandLineInterface.show_usage()
                return
            elif sys.argv[1] == '--config':
                # 加载配置后显示
                load_config()
                CommandLineInterface.show_config_info()
                return
            elif sys.argv[1] == '--stats':
                CommandLineInterface.show_file_stats()
                return
        
        # 加载配置文件
        if not load_config():
            logging.warning("使用默认配置继续运行")
        
        # 显示初始信息
        print("🔧 初始化配置...")
        CommandLineInterface.show_config_info()
        
        # 创建更新器实例
        updater = TVSourceUpdater()
        
        # 初始化
        print("🚀 初始化更新器...")
        await updater.initialize()
        
        # 执行更新
        print("📡 开始更新直播源...")
        success = await updater.update_sources()
        
        # 清理资源
        await updater.close()
        
        if success:
            print("🎉 直播源更新完成!")
            # 显示结果文件信息
            if os.path.exists(Paths.FINAL_FILE):
                stats = Utility.get_file_stats(Paths.FINAL_FILE)
                if stats["exists"]:
                    print(f"📄 结果文件: {Paths.FINAL_FILE}")
                    print(f"   频道数量: {stats.get('channel_count', 'N/A')}")
                    print(f"   文件大小: {stats['size']} bytes")
        else:
            print("❌ 直播源更新失败!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  用户中断程序")
        sys.exit(1)
    except Exception as e:
        print(f"💥 程序执行失败: {e}")
        logging.critical(f"程序执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # 运行主程序
    asyncio.run(main())
