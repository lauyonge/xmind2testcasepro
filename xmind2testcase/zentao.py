#!/usr/bin/env python
# _*_ coding:utf-8 _*_
import csv
import logging
import os

from numpy.ma.core import product

from xmind2testcase.utils import get_absolute_path
from xmind2testcase.services import get_testcase_list

"""
Convert XMind fie to Zentao testcase csv file 

Zentao official document about import CSV testcase file: https://www.zentao.net/book/zentaopmshelp/243.mhtml 
"""


def xmind_to_zentao_csv_file(xmind_file):
    """Convert XMind file to a zentao csv file"""
    xmind_file = get_absolute_path(xmind_file)
    logging.info('Start converting XMind file(%s) to zentao file...', xmind_file)
    testcases = get_testcase_list(xmind_file)

    fileheader = ["所属产品", "所属模块", "用例名称", "前置条件", "步骤", "预期", "关键词", "优先级", "执行类型", "用例类型", "适用阶段"]
    zentao_testcase_rows = [fileheader]
    for testcase in testcases:
        row = gen_a_testcase_row(testcase)
        zentao_testcase_rows.append(row)

    zentao_file = xmind_file[:-6] + '.csv'
    if os.path.exists(zentao_file):
        os.remove(zentao_file)
        # logging.info('The zentao csv file already exists, return it directly: %s', zentao_file)
        # return zentao_file

    with open(zentao_file, 'w', encoding='utf8') as f:
        writer = csv.writer(f)
        writer.writerows(zentao_testcase_rows)
        logging.info('Convert XMind file(%s) to a zentao csv file(%s) successfully!', xmind_file, zentao_file)

    return zentao_file


def gen_a_testcase_row(testcase_dict):
    # 提取产品名（从 suite 中分离）
    suite_full = testcase_dict.get('suite', '')
    if '::' in suite_full:
        product = suite_full.split('::', 1)[0]
        case_module = suite_full.split('::', 1)[1]
    else:
        product = testcase_dict.get('product', '')
        case_module = suite_full


    # case_module = gen_case_module(testcase_dict['suite'])
    case_title = testcase_dict['name']
    case_precontion = testcase_dict['preconditions']
    case_step, case_expected_result = gen_case_step_and_expected_result(testcase_dict['steps'])
    case_keyword = ''
    case_priority = gen_case_priority(testcase_dict['importance'])
    case_type  = testcase_dict.get('testcase_type', '功能测试')
    case_apply_phase = testcase_dict.get('apply_phase', '功能测试阶段')
    execution_type = gen_execution_type(testcase_dict['execution_type'])
    row = [product, case_module, case_title, case_precontion, case_step, case_expected_result, case_keyword, case_priority, execution_type, case_type, case_apply_phase]
    return row


def gen_case_module(module_name):
    if module_name:
        module_name = module_name.replace('（', '(')
        module_name = module_name.replace('）', ')')
    else:
        module_name = '/'
    return module_name


def gen_case_step_and_expected_result(steps):
    case_step = ''
    case_expected_result = ''

    for step_dict in steps:
        # 步骤
        case_step += f"{step_dict['step_number']}. {step_dict['actions'].replace('\n', '').strip()}\n"
        # 预期结果
        expected_list = step_dict.get('expectedresults') or []                              # 当值为 None 时返回空列表，join 就不会报错
        expected = '------'.join(expected_list).replace('\n', '').strip()
        case_expected_result += f"{step_dict['step_number']}. {expected}\n"                 # 没有预期结果时，添加一个空行占位

    return case_step, case_expected_result


def gen_case_priority(priority):
    """将优先级原样传递给禅道"""
    # 不做任何转换，直接返回数值字符串
    return priority


def gen_execution_type(case_type):
    mapping = {1: '手动', 2: '自动'}
    if case_type in mapping.keys():
        return mapping.get(case_type, '手动')


if __name__ == '__main__':
    xmind_file = '../docs/zentao_testcase_template.xmind'
    zentao_csv_file = xmind_to_zentao_csv_file(xmind_file)
    print('Conver the xmind file to a zentao csv file succssfully: %s', zentao_csv_file)