#!/usr/bin/env python
# -*- coding: utf-8 -*-
import csv
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


def parse_zentao_csv(csv_file_path, encoding='utf-8'):
    """
    解析禅道导出的 CSV 文件，返回结构化的用例数据。

    返回格式：
    {
        '产品名': {
            '模块A': [
                {'id': '101', 'title': '用例1', 'preconditions': '...',
                 'steps': [...], 'priority': '1', 'type': '功能测试', ...},
                ...
            ],
            '模块B': [...]
        },
        ...
    }
    """
    structure = defaultdict(lambda: defaultdict(list))
    
    try:
        with open(csv_file_path, 'r', encoding=encoding, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # 提取模块信息，去掉模块ID部分，如 "UI模块(#55)" -> "UI模块"
                module_full = row.get('所属模块', '未分类')
                if '(#' in module_full:
                    module = module_full.split('(#')[0]
                else:
                    module = module_full
                
                # 提取用例标题
                title = row.get('用例标题', '')
                
                # 提取前置条件
                preconditions = row.get('前置条件', '').replace('\r\n', '\n').replace('\r', '\n').strip()

                steps_str = row.get('步骤', '').replace('\r\n', '\n').replace('\r', '\n')
                steps = [step.strip() for step in steps_str.split('\n') if step.strip()]

                expected_str = row.get('预期', '').replace('\r\n', '\n').replace('\r', '\n')
                expected = [exp.strip() for exp in expected_str.split('\n') if exp.strip()]
                
                # 提取其他信息
                keywords = row.get('关键词', '')
                priority = row.get('优先级', '中')
                case_type = row.get('用例类型', '手动')
                stage = row.get('适用阶段', '迭代测试')
                
                # 构建用例字典
                case = {
                    'title': title,
                    'preconditions': preconditions,
                    'steps': steps,
                    'expected': expected,
                    'keywords': keywords,
                    'priority': priority,
                    'type': case_type,
                    'stage': stage
                }
                
                # 默认产品名为"默认产品"，实际应用中可能需要从CSV文件或用户输入中获取
                product = '默认产品'
                
                # 将用例添加到结构中
                structure[product][module].append(case)
                
    except Exception as e:
        logger.error(f"解析CSV文件失败: {e}")
        raise
    
    return structure

