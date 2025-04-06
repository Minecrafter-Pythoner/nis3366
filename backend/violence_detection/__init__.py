"""
暴力图像检测模块

此模块提供API用于检测图像中的暴力内容。
"""

__version__ = "0.1.0"

from .classify import ViolenceClass, get_classifier
from . import utils
from . import model