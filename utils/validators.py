"""
数据验证工具
功能：所有Agent共用的验证逻辑
包括：URL验证、日期验证、记录完整性验证、品类验证、内容哈希计算
"""

import re
import hashlib
from datetime import datetime


def validate_url(url):
    """
    验证URL格式是否正确

    参数：
        url: 待验证的URL字符串

    返回：
        (是否有效, 错误信息)
    """
    if not url:
        return False, "URL为空"

    if not url.startswith(("http://", "https://")):
        return False, "URL格式错误，必须以http://或https://开头"

    return True, ""


def check_url_accessible(url):
    """
    检查URL是否可以正常访问

    参数：
        url: 待检查的URL

    返回：
        (是否可访问, HTTP状态码, 页面标题)
    """
    import requests
    from bs4 import BeautifulSoup

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.title.string if soup.title else "无标题"
            return True, response.status_code, title.strip()
        else:
            return False, response.status_code, ""

    except requests.exceptions.Timeout:
        return False, 0, "请求超时"
    except requests.exceptions.ConnectionError:
        return False, 0, "连接失败"
    except Exception as e:
        return False, 0, str(e)


def validate_date(date_str):
    """
    验证日期格式是否正确
    支持格式：2026-05-11、2026年5月11日

    参数：
        date_str: 日期字符串

    返回：
        (是否有效, 解析后的标准格式日期, 错误信息)
    """
    if not date_str:
        return False, "", "日期为空"

    # 格式1：2026-05-11
    try:
        dt = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return True, dt.strftime("%Y-%m-%d"), ""
    except ValueError:
        pass

    # 格式2：2026年5月11日
    match_cn = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日", date_str.strip())
    if match_cn:
        year, month, day = match_cn.groups()
        try:
            dt = datetime(int(year), int(month), int(day))
            return True, dt.strftime("%Y-%m-%d"), ""
        except ValueError:
            pass

    # 格式3：2026年（只有年份）
    match_year = re.match(r"(\d{4})年$", date_str.strip())
    if match_year:
        return True, f"{match_year.group(1)}-01-01", "只有年份，已设为1月1日"

    return False, "", f"无法解析日期格式：{date_str}"


def validate_record(record, required_fields):
    """
    验证单条记录的完整性

    参数：
        record: 数据记录字典
        required_fields: 必填字段列表

    返回：
        (是否完整, 缺失字段列表)
    """
    missing_fields = []

    for field in required_fields:
        value = record.get(field)
        if not value or value in ["未明确", "", None]:
            missing_fields.append(field)

    return len(missing_fields) == 0, missing_fields


def calculate_completeness_score(record, all_fields):
    """
    计算记录的完整性得分

    参数：
        record: 数据记录字典
        all_fields: 所有字段列表

    返回：
        完整性得分（0-100）
    """
    if not all_fields:
        return 0

    filled_count = 0
    for field in all_fields:
        value = record.get(field)
        if value and value not in ["未明确", "", None]:
            filled_count += 1

    return round(filled_count / len(all_fields) * 100, 2)


def validate_cell_category(product_name, business_scope=""):
    """
    验证产品是否属于细胞治疗领域
    采用至少两个独立信号原则

    参数：
        product_name: 产品名称
        business_scope: 企业经营范围

    返回：
        (验证状态, 信号列表)
    """
    signals = []

    # 细胞品类关键词
    cell_keywords = [
        "CAR-T", "CAR-NK", "TCR-T", "TIL",
        "细胞注射液", "细胞治疗", "干细胞",
        "间充质", "嵌合抗原受体", "免疫细胞",
        "仑赛"
    ]

    # 检查产品名称
    for keyword in cell_keywords:
        if keyword in product_name:
            signals.append(f"产品名称包含'{keyword}'")
            break

    # 检查经营范围
    biz_keywords = ["细胞", "干细胞", "基因治疗", "免疫治疗"]
    for keyword in biz_keywords:
        if keyword in business_scope:
            signals.append(f"经营范围包含'{keyword}'")
            break

    # 判定
    if len(signals) >= 2:
        return "已验证", signals
    elif len(signals) == 1:
        return "待人工审核", signals
    else:
        return "未通过", signals


def verify_lunsai_keyword(product_name, additional_info=""):
    """
    特别验证仑赛类关键词
    因为仑赛可能是细胞产品，也可能是其他药品

    参数：
        product_name: 产品名称
        additional_info: 额外信息（适应症、企业信息等）

    返回：
        (是否为细胞产品, 验证依据)
    """
    if "仑赛" not in product_name:
        return None, []

    validation_basis = []

    # 验证1：检查是否有细胞字样
    if "细胞" in product_name:
        validation_basis.append("产品名称包含'细胞'")

    # 验证2：检查适应症是否为肿瘤或血液病
    tumor_keywords = ["肿瘤", "癌", "白血病", "淋巴瘤", "骨髓瘤", "血液"]
    for keyword in tumor_keywords:
        if keyword in additional_info:
            validation_basis.append(f"适应症包含'{keyword}'")
            break

    # 验证3：检查企业是否有细胞相关业务
    cell_biz_keywords = ["细胞", "免疫", "CAR"]
    for keyword in cell_biz_keywords:
        if keyword in additional_info:
            validation_basis.append(f"企业信息包含'{keyword}'")
            break

    # 判定
    if len(validation_basis) >= 2:
        return True, validation_basis
    else:
        return False, validation_basis


def calculate_hash(text):
    """
    计算文本的MD5哈希值
    用于判断法规内容是否变化（增量更新机制）

    参数：
        text: 待计算的文本

    返回：
        MD5哈希字符串
    """
    if not text:
        return ""

    return hashlib.md5(text.encode('utf-8')).hexdigest()


def get_current_date():
    """
    获取当前日期
    返回：YYYY-MM-DD 格式
    """
    return datetime.now().strftime("%Y-%m-%d")


def get_current_datetime():
    """
    获取当前日期时间
    返回：YYYY-MM-DD HH:MM:SS 格式
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
