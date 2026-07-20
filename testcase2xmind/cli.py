#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import logging
import os

from testcase2xmind.parser import parse_zentao_csv
from testcase2xmind.generator import generate_xmind

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """
    命令行入口函数
    """
    parser = argparse.ArgumentParser(description='Convert Zentao CSV testcase file to XMind mind map')
    
    # 添加参数
    parser.add_argument('csv_file', help='Zentao exported CSV testcase file path')
    parser.add_argument('-o', '--output', help='Output XMind file path', default=None)
    parser.add_argument('-e', '--encoding', help='CSV file encoding', default='utf-8')
    
    # 解析参数
    args = parser.parse_args()
    
    # 检查CSV文件是否存在
    if not os.path.exists(args.csv_file):
        logger.error(f"CSV文件不存在: {args.csv_file}")
        return 1
    
    # 确定输出文件路径
    if args.output:
        output_file = args.output
    else:
        # 默认输出文件名为CSV文件名的xmind版本
        base_name = os.path.splitext(args.csv_file)[0]
        output_file = f"{base_name}.xmind"
    
    try:
        logger.info(f"开始解析CSV文件: {args.csv_file}")
        # 解析CSV文件
        testcase_structure = parse_zentao_csv(args.csv_file, args.encoding)
        
        logger.info(f"开始生成XMind文件: {output_file}")
        # 生成XMind文件
        generate_xmind(testcase_structure, output_file)
        
        logger.info(f"转换完成！XMind文件已保存至: {output_file}")
        return 0
        
    except Exception as e:
        logger.error(f"转换失败: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
