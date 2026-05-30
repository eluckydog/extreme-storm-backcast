# -*- coding: utf-8 -*-
"""Compatibility layer — 让 carrington.dst_model 指向 dst_model_v2"""

from .dst_model_v2 import DstEvolutionModelV2 as DstEvolutionModel

# 如果 cross_calibrate.py 也用了 DstProfile，提供一个空兼容类
class DstProfile:
    """Stub — dst_model_v2 不再使用 DstProfile"""
    pass

__all__ = ['DstEvolutionModel', 'DstProfile']
