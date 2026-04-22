#!/usr/bin/env python
# _*_ coding:utf-8 _*_


TAG_XML = 'xml'
TAG_JSON = 'json'

TAG_TESTSUITE = 'testsuite'
TAG_DETAILS = 'details'

TAG_TESTCASE = 'testcase'
TAG_VERSION = 'version'
TAG_SUMMARY = 'summary'
TAG_PRECONDITIONS = 'preconditions'
TAG_IMPORTANCE = 'importance'
TAG_ESTIMATED_EXEC_DURATION = 'estimated_exec_duration'
TAG_STATUS = 'status'
TAG_IS_OPEN = 'is_open'
TAG_ACTIVE = 'active'
TAG_STEPS = 'steps'
TAG_STEP = 'step'
TAG_STEP_NUMBER = 'step_number'
TAG_ACTIONS = 'actions'
TAG_EXPECTEDRESULTS = 'expectedresults'
TAG_EXECUTION_TYPE = 'execution_type'

ATTR_NMAE = 'name'
ATTR_ID = 'id'
ATTR_INTERNALID = 'internalid'

# -- boyi --
PRECONDITIONS_TAG = '前置条件'
TESTCASE_TAG = '测试用例'
TESTCASE_IGNORE_TAGS = ['ignore', 'skipped']
TESTSTEP_TAG = '执行步骤'
EXPECT_RESULT_TAG = '预期结果'


# ==================== 用例类型相关 ====================
# 用例类型标签
TESTCASE_TYPE_TAG = '用例类型'

# 用例类型枚举（用于解析时的值验证）
TESTCASE_TYPE_ENUM = [
    '单元测试',
    '接口测试',
    '功能测试',
    '安装部署',
    '配置相关',
    '性能测试',
    '安全相关',
    '其他'
]

# 用例类型默认值
DEFAULT_TESTCASE_TYPE = '功能测试'


# ==================== 适用阶段相关 ====================
# 适用阶段标签
APPLY_PHASE_TAG = '适用阶段'

# 适用阶段枚举
APPLY_PHASE_ENUM = [
    '单元测试阶段',
    '功能测试阶段',
    '集成测试阶段',
    '系统测试阶段',
    '冒烟测试阶段',
    '版本验证阶段'
]

# 适用阶段默认值
DEFAULT_APPLY_PHASE = '功能测试阶段'

# 如果禅道导入时需要用数字代码，可以添加映射
TESTCASE_TYPE_ZENTAO_MAPPING = {
    '单元测试': 'unit',
    '接口测试': 'api',
    '功能测试': 'functional',
    '安装部署': 'deployment',
    '配置相关': 'config',
    '性能测试': 'performance',
    '安全相关': 'security',
    '其他': 'other'
}

APPLY_PHASE_ZENTAO_MAPPING = {
    '单元测试阶段': 'unit',
    '功能测试阶段': 'functional',
    '集成测试阶段': 'integration',
    '系统测试阶段': 'system',
    '冒烟测试阶段': 'smoke',
    '版本验证阶段': 'version'
}

# ==================== 优先级相关 ====================
# 优先级标签匹配规则
IMPORTANCE_TAGS = ['P[0-9]', 'priority-[0-9]', 'priority [0-9]']

# 默认优先级
DEFAULT_PRIORITY = 3  # 默认为"中"


# ==================== 执行类型相关 ====================
# 执行类型标签
EXECUTION_MANUAL_TYPE_TAG = ['手动', '手工', 'manual']
EXECUTION_AUTO_TYPE_TAG = ['自动', 'auto', 'automate', 'automation']

# 手动
EXECUTION_MANUAL_TYPE = 1

# 自动
EXECUTION_AUTO_TYPE = 2

config = {'sep': '<font color="red"> >> </font>',
          'valid_sep': '&>+/-',
          'precondition_sep': '\n && \n',
          'summary_sep': '\n----\n',
          'step': '\n#####\n',
          'ignore_char': '#!！'
          }
