"""
日志工具
功能：统一的日志输出格式，方便调试和追踪Agent运行状态
输出：控制台 + 文件（logs/目录）
"""

import logging
import os
from datetime import datetime


def setup_logger(name, log_file=None, level=logging.INFO):
    """
    设置日志记录器

    参数：
        name: 日志记录器名称（如 agent_1）
        log_file: 日志文件路径（可选）
        level: 日志级别（DEBUG/INFO/WARNING/ERROR）

    返回：
        logger对象
    """
    # 创建日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加handler
    if logger.handlers:
        return logger

    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件输出（如果指定了日志文件）
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_agent_logger(agent_name):
    """
    获取Agent专用的日志记录器
    日志文件按日期命名，保存到 logs/ 目录

    参数：
        agent_name: Agent名称（如 agent_1, agent_2）

    返回：
        logger对象
    """
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(log_dir, f"{agent_name}_{timestamp}.log")

    return setup_logger(agent_name, log_file)
