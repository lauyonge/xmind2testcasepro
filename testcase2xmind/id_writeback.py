import csv
import json
import logging
import os
import shutil
import tempfile
import zipfile

logger = logging.getLogger(__name__)


def build_id_map_from_csv(csv_file_path):
    """
    从禅道导出的CSV文件中，构建一个标题->ID的映射字典。
    """
    id_map = {}
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            dialect = csv.Sniffer().sniff(f.read(1024))
            f.seek(0)
            reader = csv.DictReader(f, dialect=dialect)

            if '用例名称' not in reader.fieldnames or '用例ID' not in reader.fieldnames:
                logger.error("CSV文件中缺少 '用例名称' 或 '用例ID' 列，请检查是否为禅道导出的标准模板。")
                return {}

            for row_num, row in enumerate(reader, start=2):
                case_title = row.get('用例名称')
                case_id = row.get('用例ID')
                if case_title and case_id:
                    id_map[case_title.strip()] = case_id.strip()
                else:
                    logger.debug("第%d行跳过：标题或ID为空", row_num)
    except FileNotFoundError:
        logger.error("CSV文件未找到: %s", csv_file_path)
    except Exception as e:
        logger.exception("读取CSV文件时发生未知异常: %s", e)
    logger.info("从CSV文件 '%s' 中成功加载了 %d 个用例ID映射。", os.path.basename(csv_file_path), len(id_map))
    return id_map


def _update_topic_ids(topic, id_map, updated_count):
    """
    递归遍历XMind节点，根据标题匹配更新ID。
    """
    title = topic.get('title', '')
    if title and title in id_map:
        topic['id'] = id_map[title]
        updated_count[0] += 1
        logger.debug("已更新节点 '%s' 的ID为: %s", title, id_map[title])

    children = topic.get('children', {}).get('attached', [])
    for child in children:
        _update_topic_ids(child, id_map, updated_count)


def write_ids_to_xmind(xmind_path, csv_path, output_path=None):
    """
    将CSV中的ID写回XMind文件的对应节点。
    """
    logger.info("开始执行用例ID回填任务...")
    logger.info("源XMind文件: %s", xmind_path)
    logger.info("源CSV文件: %s", csv_path)

    id_map = build_id_map_from_csv(csv_path)
    if not id_map:
        logger.warning("未从CSV中提取到任何ID，任务终止。")
        return

    if output_path is None:
        base_name = os.path.splitext(xmind_path)[0]
        output_path = f"{base_name}_with_ids.xmind"

    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp()
        logger.debug("创建临时目录: %s", temp_dir)

        with zipfile.ZipFile(xmind_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        content_json_path = os.path.join(temp_dir, 'content.json')
        if not os.path.exists(content_json_path):
            logger.error("XMind文件中未找到 content.json，无法进行ID回填。")
            return

        with open(content_json_path, 'r', encoding='utf-8') as f:
            content_data = json.load(f)

        updated_count = [0]
        for sheet in content_data:
            root_topic = sheet.get('rootTopic', {})
            _update_topic_ids(root_topic, id_map, updated_count)

        with open(content_json_path, 'w', encoding='utf-8') as f:
            json.dump(content_data, f, ensure_ascii=False, indent=2)

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_out:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zip_out.write(file_path, arcname)

        logger.info("ID回填完成！共更新 %d 个节点。输出文件: %s", updated_count[0], output_path)
        return output_path

    except Exception as e:
        logger.exception("ID回填过程中发生异常: %s", e)
        raise
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.debug("已清理临时目录: %s", temp_dir)
