#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import tempfile
import zipfile
import uuid
import time
from datetime import datetime

import xmind
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)


def _gen_id():
    return uuid.uuid4().hex[:26]


def _current_timestamp():
    return int(time.time() * 1000)


def _current_time_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _build_meta_xml():
    return '<?xml version="1.0" encoding="UTF-8" standalone="no"?>' \
           '<meta xmlns="urn:xmind:xmap:xmlns:meta:2.0" version="2.0">' \
           '<Author><Name/><Email/><Org/></Author>' \
           '<Create><Time>{}</Time></Create>' \
           '<Creator><Name>XMind2TestCasePro</Name><Version>1.0</Version></Creator>' \
           '<Thumbnail><Origin><X>0</X><Y>0</Y></Origin>' \
           '<BackgroundColor>#FFFFFF</BackgroundColor></Thumbnail>' \
           '</meta>'.format(_current_time_str())


def _build_styles_xml():
    return '<?xml version="1.0" encoding="UTF-8" standalone="no"?>' \
           '<xmap-styles xmlns="urn:xmind:xmap:xmlns:style:2.0" ' \
           'xmlns:fo="http://www.w3.org/1999/XSL/Format" ' \
           'xmlns:svg="http://www.w3.org/2000/svg" version="2.0">' \
           '<styles/>' \
           '<automatic-styles/>' \
           '</xmap-styles>'


def _build_comments_xml():
    return '<?xml version="1.0" encoding="UTF-8" standalone="no"?>' \
           '<comments xmlns="urn:xmind:xmap:xmlns:comments:2.0" version="2.0"/>'


def _build_manifest_xml():
    return '<?xml version="1.0" encoding="UTF-8" standalone="no"?>' \
           '<manifest xmlns="urn:xmind:xmap:xmlns:manifest:1.0" password-hint="">' \
           '<file-entry full-path="comments.xml" media-type=""/>' \
           '<file-entry full-path="content.xml" media-type="text/xml"/>' \
           '<file-entry full-path="META-INF/" media-type=""/>' \
           '<file-entry full-path="META-INF/manifest.xml" media-type="text/xml"/>' \
           '<file-entry full-path="meta.xml" media-type="text/xml"/>' \
           '<file-entry full-path="styles.xml" media-type="text/xml"/>' \
           '</manifest>'


def generate_xmind(testcase_structure, output_file):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_xmind = os.path.join(temp_dir, 'temp.xmind')

            workbook = xmind.load(temp_xmind)
            if not workbook.getSheets():
                sheet = workbook.createSheet()
            else:
                sheet = workbook.getSheets()[0]

            for product_name, modules in testcase_structure.items():
                root_topic = sheet.getRootTopic()
                root_topic.setTitle(product_name)

                for module_name, cases in modules.items():
                    module_topic = root_topic.addSubTopic()
                    module_topic.setTitle(module_name)

                    for case in cases:
                        case_topic = module_topic.addSubTopic()
                        case_topic.setTitle(case['title'])

                        if case['preconditions']:
                            pre_topic = case_topic.addSubTopic()
                            pre_topic.setTitle("前置条件：{}".format(case['preconditions']))

                        if case['steps']:
                            for i, step in enumerate(case['steps'], 1):
                                step_topic = case_topic.addSubTopic()
                                step_topic.setTitle("测试步骤：{}".format(step))

                                if i <= len(case['expected']):
                                    exp = case['expected'][i - 1]
                                    if exp and not exp.rstrip('.').isdigit():
                                        exp_topic = case_topic.addSubTopic()
                                        exp_topic.setTitle("预期结果：{}".format(exp))

                        if case['keywords']:
                            keywords_topic = case_topic.addSubTopic()
                            keywords_topic.setTitle("关键词: {}".format(case['keywords']))

                        info_topic = case_topic.addSubTopic()
                        info_topic.setTitle(
                            "优先级: {} | 类型: {} | 阶段: {}".format(
                                case['priority'], case['type'], case['stage']
                            )
                        )

            xmind.save(workbook, temp_xmind)

            with zipfile.ZipFile(temp_xmind, 'r') as zin:
                content_xml = zin.read('content.xml')
                styles_xml = zin.read('styles.xml') if 'styles.xml' in zin.namelist() else _build_styles_xml()
                comments_xml = zin.read('comments.xml') if 'comments.xml' in zin.namelist() else _build_comments_xml()

            with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zout:
                zout.writestr('content.xml', content_xml)
                zout.writestr('styles.xml', styles_xml)
                zout.writestr('comments.xml', comments_xml)
                zout.writestr('meta.xml', _build_meta_xml())
                zout.writestr('META-INF/manifest.xml', _build_manifest_xml())

            logger.info("XMind文件生成成功: {}".format(output_file))
            return output_file

    except Exception as e:
        logger.error("生成XMind文件失败: {}".format(e))
        raise
