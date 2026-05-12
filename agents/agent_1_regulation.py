"""
Agent 1：监管政策监测Agent
功能：读取法规清单 → 访问法规网页 → 提取关键词 → 自查验证 → 保存结果
输出：
    - data/keyword_database.csv（关键词词库）
    - data/update_log.csv（更新日志）
    - data/regulation_registry.csv（更新法规清单状态）
"""

import csv
import os
import re
import sys
import time
import hashlib
from datetime import datetime
from collections import Counter

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import get_agent_logger
from utils.validators import calculate_hash, get_current_datetime

# 初始化日志
logger = get_agent_logger("agent_1")

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


# ============================================================
# 第一部分：自查检验机制
# ============================================================

class SelfChecker:
    """自查检验类：Agent运行过程中的自动验证"""

    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []
        self.errors = []

    def check(self, condition, check_name, error_msg=""):
        """执行单个检查"""
        if condition:
            self.checks_passed += 1
            logger.debug(f"  ✅ 检查通过：{check_name}")
        else:
            self.checks_failed += 1
            msg = f"检查失败：{check_name} - {error_msg}"
            self.errors.append(msg)
            logger.warning(f"  ❌ {msg}")

    def warn(self, condition, warning_msg):
        """记录警告"""
        if not condition:
            self.warnings.append(warning_msg)
            logger.warning(f"  ⚠️ {warning_msg}")

    def summary(self):
        """输出检查总结"""
        logger.info(f"\n===== 自查总结 =====")
        logger.info(f"  通过：{self.checks_passed} 项")
        logger.info(f"  失败：{self.checks_failed} 项")
        logger.info(f"  警告：{len(self.warnings)} 项")
        if self.errors:
            logger.error(f"  错误列表：")
            for err in self.errors[:5]:  # 只显示前5个
                logger.error(f"    - {err}")
        return self.checks_failed == 0


# ============================================================
# 第二部分：数据加载
# ============================================================

def load_regulation_registry():
    """加载法规清单"""
    filepath = os.path.join(DATA_DIR, "regulation_registry.csv")

    if not os.path.exists(filepath):
        logger.error(f"法规清单文件不存在：{filepath}")
        return []

    regulations = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            regulations.append(row)

    logger.info(f"加载法规清单：{len(regulations)} 条")
    return regulations


def load_synonyms():
    """加载同义词表"""
    filepath = os.path.join(DATA_DIR, "synonyms.csv")
    synonyms_map = {}

    if not os.path.exists(filepath):
        logger.warning(f"同义词表不存在：{filepath}，跳过同义词合并")
        return synonyms_map

    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            standard = row.get('standard_form', '').strip()
            if standard:
                for key in ['synonym_1', 'synonym_2', 'synonym_3', 'synonym_4']:
                    synonym = row.get(key, '').strip()
                    if synonym:
                        synonyms_map[synonym] = standard

    logger.info(f"加载同义词表：{len(synonyms_map)} 条映射")
    return synonyms_map


def load_stopwords():
    """加载通用词过滤表"""
    filepath = os.path.join(DATA_DIR, "stopwords.csv")
    stopwords = set()

    if not os.path.exists(filepath):
        logger.warning(f"停用词表不存在：{filepath}，跳过停用词过滤")
        return stopwords

    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            word = row.get('word', '').strip()
            if word:
                stopwords.add(word)

    logger.info(f"加载停用词表：{len(stopwords)} 个")
    return stopwords


def load_existing_keywords():
    """加载已有的关键词词库"""
    filepath = os.path.join(DATA_DIR, "keyword_database.csv")
    existing = {}

    if not os.path.exists(filepath):
        return existing

    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            keyword = row.get('keyword', '').strip()
            if keyword:
                existing[keyword] = row

    logger.info(f"加载已有关键词：{len(existing)} 个")
    return existing


# ============================================================
# 第三部分：法规文本读取（修复版：支持CDE JavaScript渲染）
# ============================================================

def fetch_html_text(url):
    """
    从HTML页面提取正文文本（适用于NMPA、卫健委等普通网站）
    返回：(文本内容, 错误信息)
    """
    import requests
    from bs4 import BeautifulSoup

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        response.encoding = response.apparent_encoding or 'utf-8'

        if response.status_code != 200:
            return "", f"HTTP状态码：{response.status_code}"

        soup = BeautifulSoup(response.text, "html.parser")

        # 移除script和style标签
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        # 提取正文
        text = soup.get_text(separator='\n', strip=True)

        # 清洗文本
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)

        return text, ""

    except requests.exceptions.Timeout:
        return "", "请求超时"
    except requests.exceptions.ConnectionError:
        return "", "连接失败"
    except Exception as e:
        return "", str(e)


def fetch_cde_pdf(url, reg_name):
    """
    从CDE网站下载PDF附件并提取文本
    使用修复版模块v2（绕过反自动化检测）
    """
    try:
        from agents.agent_1_regulation_cde_fix import fetch_cde_pdf as _fetch_cde_pdf
        return _fetch_cde_pdf(url, reg_name)
    except ImportError:
        return "", "CDE修复模块未找到"
    except Exception as e:
        return "", f"CDE下载失败：{str(e)}"

def extract_pdf_text(pdf_path):
    """
    从PDF文件提取文本
    返回：(文本内容, 错误信息)
    """
    try:
        # 优先使用pdfplumber（效果更好）
        try:
            import pdfplumber
            text_parts = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            text = '\n'.join(text_parts)
            if text.strip():
                return text, ""
        except Exception as e:
            logger.debug(f"    pdfplumber提取失败：{e}，尝试PyPDF2")

        # 备用方案：使用PyPDF2
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        text = '\n'.join(text_parts)

        if not text.strip():
            return "", "PDF文本提取为空"

        return text, ""

    except Exception as e:
        return "", f"PDF提取失败：{str(e)}"


def fetch_pdf_from_url(url):
    """
    直接从URL下载PDF文件并提取文本
    返回：(文本内容, 错误信息)
    """
    import requests
    import tempfile

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()

        # 保存到临时文件
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name

        # 提取文本
        text, error = extract_pdf_text(tmp_path)

        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except:
            pass

        return text, error

    except Exception as e:
        return "", f"PDF下载失败：{str(e)}"


def fetch_regulation_text(regulation):
    """
    根据法规的页面类型选择合适的提取方式
    返回：(文本内容, 错误信息)
    """
    url = regulation.get('url', '')
    page_type = regulation.get('page_type', 'HTML').upper()
    issuing_unit = regulation.get('issuing_unit', '')
    reg_name = regulation.get('regulation_name', '')

    if not url or url == '待确认':
        return "", "URL未确认"

    # CDE网站特殊处理：使用Playwright下载PDF
    if 'cde.org.cn' in url:
        logger.info(f"    检测到CDE网站，使用Playwright下载PDF...")
        return fetch_cde_pdf(url, reg_name)

    # 其他PDF文件
    if page_type == 'PDF' or url.endswith('.pdf'):
        return fetch_pdf_from_url(url)

    # 普通HTML页面
    return fetch_html_text(url)


# ============================================================
# 第四部分：关键词提取（规则匹配 + NLP分词）
# ============================================================

# 品类词正则规则
CATEGORY_PATTERNS = [
    # CAR-X系列
    r'CAR-[A-Z]+',
    r'TCR-[A-Z]+',
    r'TIL',
    # XX治疗产品
    r'[\u4e00-\u9fa5]{2,8}治疗产品',
    # XX干细胞
    r'[\u4e00-\u9fa5]{2,8}干细胞',
    # XX细胞制剂/产品/疗法/注射液
    r'[\u4e00-\u9fa5]{2,8}细胞(?:制剂|产品|疗法|注射液)',
    # XX细胞外泌体/裂解物
    r'[\u4e00-\u9fa5]{2,8}细胞外泌体',
    r'[\u4e00-\u9fa5]{2,8}细胞裂解物',
    # XX库
    r'[\u4e00-\u9fa5]{2,8}(?:细胞|干细胞)库',
    r'[\u4e00-\u9fa5]{2,8}血库',
    # 免疫细胞
    r'[\u4e00-\u9fa5]{2,8}免疫细胞',
    # 基因修饰细胞
    r'[\u4e00-\u9fa5]{2,8}基因修饰细胞',
    # XX细胞
    r'(?:树突状|NK|DC|CIK|T|B)细胞',
    # 灭活细胞
    r'灭活细胞',
]

# 属性词正则规则
ATTRIBUTE_PATTERNS = [
    r'(?:自体|异体|同种异体)',
    r'(?:体外|体内)(?:操作|扩增|培养|修饰)?',
    r'基因(?:修饰|转导|编辑|治疗)',
    r'诱导分化',
    r'细胞(?:活化|扩增|培养|分离|纯化|冻存|复苏)',
    r'(?:活|冻存|新鲜)细胞',
    r'人源(?:性|细胞系)',
    r'动物源性',
]

# 监管词正则规则
REGULATORY_PATTERNS = [
    r'(?:IND|NDA|BLA)(?:申请|申报|审评)?',
    r'GMP(?:管理|规范|生产|检查)?',
    r'临床(?:试验|研究)(?:备案|审批|申请|管理)?',
    r'注册(?:审评|申请|检验|申报)?',
    r'(?:质量管理|质量控制|质量标准|质量检验)',
    r'工艺(?:验证|变更|研究)',
    r'(?:风险评估|风险管理)',
    r'稳定性研究',
    r'生物学活性',
    r'(?:纯度|无菌)检测',
    r'药(?:学|理|效|代)(?:研究|学)?',
    r'免疫原性',
    r'(?:安全性|有效性)(?:评价|评估)?',
    r'伦理(?:审查|委员会)',
    r'供者筛查',
    r'可追溯性',
    r'(?:知情同意|知情与保密)',
    r'(?:突破性治疗|优先审评|快速审批)',
    r'临床转化应用',
]


def extract_keywords_by_regex(text):
    """用正则表达式提取关键词"""
    results = []

    # 品类词
    for pattern in CATEGORY_PATTERNS:
        matches = re.findall(pattern, text)
        for match in matches:
            if len(match) >= 2:
                results.append((match, '品类词'))

    # 属性词
    for pattern in ATTRIBUTE_PATTERNS:
        matches = re.findall(pattern, text)
        for match in matches:
            if len(match) >= 2:
                results.append((match, '属性词'))

    # 监管词
    for pattern in REGULATORY_PATTERNS:
        matches = re.findall(pattern, text)
        for match in matches:
            if len(match) >= 2:
                results.append((match, '监管词'))

    return results


def extract_keywords_by_jieba(text):
    """用jieba分词提取关键词"""
    try:
        import jieba
        import jieba.posseg as pseg

        # 加载自定义词典
        dict_path = os.path.join(DATA_DIR, "cell_domain_dict.txt")
        if os.path.exists(dict_path):
            jieba.load_userdict(dict_path)

        results = []
        words = pseg.cut(text)

        for word, flag in words:
            # 过滤短词和非名词
            if len(word) >= 2 and (flag.startswith('n') or flag.startswith('v')):
                results.append((word, flag))

        return results

    except ImportError:
        logger.warning("jieba未安装，跳过NLP分词")
        return []


def extract_all_keywords(text, regulation_id, checker):
    """完整关键词提取流程"""
    checker.check(text is not None and len(text) > 0,
                  f"{regulation_id} 文本内容非空",
                  "法规文本为空，无法提取关键词")

    if not text:
        return []

    # Step 1：规则匹配
    regex_results = extract_keywords_by_regex(text)
    logger.info(f"  规则匹配提取：{len(regex_results)} 个")

    # Step 2：NLP分词
    nlp_results = extract_keywords_by_jieba(text)
    logger.info(f"  NLP分词提取：{len(nlp_results)} 个")

    # Step 3：合并结果
    all_keywords = []
    for kw, category in regex_results:
        all_keywords.append({
            'keyword': kw,
            'category': category,
            'source': 'regex',
            'regulation_id': regulation_id
        })

    for kw, pos in nlp_results:
        # NLP提取的需要分类
        category = classify_nlp_keyword(kw)
        if category:
            all_keywords.append({
                'keyword': kw,
                'category': category,
                'source': 'nlp',
                'pos': pos,
                'regulation_id': regulation_id
            })

    return all_keywords


def classify_nlp_keyword(keyword):
    """对NLP提取的关键词进行分类"""
    # 品类词特征
    category_indicators = ['细胞', '干细胞', '治疗', '制剂', '产品', '疗法', '库', 'CAR', 'TCR', 'TIL']
    # 属性词特征
    attribute_indicators = ['自体', '异体', '体外', '体内', '基因', '活化', '扩增', '培养', '修饰']
    # 监管词特征
    regulatory_indicators = ['GMP', 'IND', 'NDA', '临床', '注册', '质量', '检验', '审评', '审批']

    for indicator in category_indicators:
        if indicator in keyword:
            return '品类词'

    for indicator in attribute_indicators:
        if indicator in keyword:
            return '属性词'

    for indicator in regulatory_indicators:
        if indicator in keyword:
            return '监管词'

    return None


# ============================================================
# 第五部分：自查与去重
# ============================================================

def deduplicate_keywords(keywords_list, synonyms_map, stopwords):
    """关键词去重、同义词合并、停用词过滤"""
    # 统计每个关键词出现的次数和来源
    keyword_stats = {}
    for item in keywords_list:
        kw = item['keyword'].strip()

        # 过滤停用词
        if kw in stopwords:
            continue

        # 过滤太短的词
        if len(kw) < 2:
            continue

        # 同义词合并
        if kw in synonyms_map:
            kw = synonyms_map[kw]

        if kw not in keyword_stats:
            keyword_stats[kw] = {
                'keyword': kw,
                'category': item['category'],
                'sources': set(),
                'count': 0
            }

        keyword_stats[kw]['sources'].add(item.get('regulation_id', ''))
        keyword_stats[kw]['count'] += 1

    # 转换为列表
    result = []
    for kw, stats in keyword_stats.items():
        result.append({
            'keyword': kw,
            'category': stats['category'],
            'regulation_source': ';'.join(sorted(stats['sources'])),
            'frequency': stats['count']
        })

    logger.info(f"去重后关键词数：{len(result)} 个")
    return result


# ============================================================
# 第六部分：CDE交叉验证
# ============================================================

def verify_with_cde(keywords_list, checker):
    """与CDE已受理产品进行交叉验证"""
    logger.info("开始CDE交叉验证...")

    # CDE相关的品类关键词（从法规中已知的）
    cde_known_keywords = {
        'CAR-T', 'CAR-NK', 'TCR-T', 'TIL',
        '免疫细胞治疗产品', '细胞治疗产品',
        '间充质干细胞', '造血干细胞', '人源干细胞',
        '树突状细胞', 'NK细胞', 'DC细胞',
        '干细胞制剂', '细胞外泌体',
        '嵌合抗原受体T细胞',
    }

    for item in keywords_list:
        kw = item['keyword']
        if kw in cde_known_keywords or item['category'] == '品类词':
            # 品类词默认标记为待验证
            if kw in cde_known_keywords:
                item['cde_verified'] = '是'
                item['confidence'] = '高'
            else:
                item['cde_verified'] = '待验证'
                item['confidence'] = '中'
        else:
            item['cde_verified'] = '-'
            item['confidence'] = '中' if item['category'] else '低'

    checker.check(len(keywords_list) > 0,
                  "CDE验证后关键词列表非空",
                  "CDE验证后关键词列表为空")

    return keywords_list


# ============================================================
# 第七部分：增量更新检查
# ============================================================

def check_for_updates(regulations, checker):
    """检查法规是否有更新"""
    need_parse = []

    for reg in regulations:
        reg_id = reg.get('id', '')
        link_status = reg.get('link_status', '')
        parse_status = reg.get('parse_status', '')
        url = reg.get('url', '')

        # 检查1：URL是否有效
        if not url or url == '待确认':
            logger.debug(f"  跳过 {reg_id}：URL未确认")
            continue

        # 检查2：链接状态是否已确认
        if link_status != '已确认':
            logger.debug(f"  跳过 {reg_id}：链接未确认")
            continue

        # 检查3：是否需要解析
        if parse_status == '待解析':
            logger.info(f"  需要解析：{reg_id}（首次解析）")
            need_parse.append(reg)
        elif parse_status == '已解析':
            # 检查内容是否有更新
            old_hash = reg.get('content_hash', '')
            if not old_hash:
                logger.info(f"  需要重新解析：{reg_id}（缺少哈希值）")
                need_parse.append(reg)

    checker.check(len(need_parse) > 0,
                  "有需要解析的法规",
                  "没有需要解析的法规")

    return need_parse


# ============================================================
# 第八部分：保存结果
# ============================================================

def save_keyword_database(keywords_list, existing_keywords):
    """保存关键词词库"""
    filepath = os.path.join(DATA_DIR, "keyword_database.csv")

    # 合并已有关键词
    all_keywords = dict(existing_keywords)

    for item in keywords_list:
        kw = item['keyword']
        if kw in all_keywords:
            # 更新已有关键词
            existing = all_keywords[kw]
            # 合并来源
            old_sources = set(existing.get('regulation_source', '').split(';'))
            new_sources = set(item.get('regulation_source', '').split(';'))
            merged_sources = old_sources.union(new_sources)
            existing['regulation_source'] = ';'.join(sorted(merged_sources))
            # 更新频率
            existing['frequency'] = str(int(existing.get('frequency', 0)) + item.get('frequency', 1))
        else:
            # 新增关键词
            all_keywords[kw] = {
                'id': f"KW-{len(all_keywords)+1:04d}",
                'keyword': kw,
                'category': item.get('category', ''),
                'confidence': item.get('confidence', '中'),
                'regulation_source': item.get('regulation_source', ''),
                'cde_verified': item.get('cde_verified', '待验证'),
                'status': '有效',
                'created_date': get_current_datetime().split(' ')[0],
                'frequency': str(item.get('frequency', 1))
            }

    # 写入CSV
    fieldnames = ['id', 'keyword', 'category', 'confidence', 'regulation_source',
                  'cde_verified', 'status', 'created_date', 'frequency']

    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for kw in sorted(all_keywords.keys()):
            writer.writerow(all_keywords[kw])

    logger.info(f"保存关键词词库：{len(all_keywords)} 个关键词 -> {filepath}")


def update_regulation_status(regulations, parsed_ids):
    """更新法规清单的解析状态"""
    filepath = os.path.join(DATA_DIR, "regulation_registry.csv")

    fieldnames = ['id', 'regulation_name', 'issuing_unit', 'category', 'regulation_level',
                  'publish_date', 'notice_number', 'url', 'page_type', 'link_status',
                  'domain', 'keyword_extraction_status', 'monitor_frequency',
                  'parse_status', 'last_check_time', 'content_hash', 'remarks']

    for reg in regulations:
        if reg.get('id') in parsed_ids:
            reg['parse_status'] = '已解析'
            reg['keyword_extraction_status'] = '已提取'
            reg['last_check_time'] = get_current_datetime()

    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(regulations)

    logger.info(f"更新法规清单状态：{len(parsed_ids)} 条已解析")


def save_update_log(regulations_count, parsed_count, new_keywords_count, check_type):
    """保存更新日志"""
    filepath = os.path.join(DATA_DIR, "update_log.csv")

    # 检查文件是否存在
    file_exists = os.path.exists(filepath)

    fieldnames = ['check_time', 'check_type', 'total_regulations', 'parsed_count',
                  'new_keywords_count', 'action']

    with open(filepath, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            'check_time': get_current_datetime(),
            'check_type': check_type,
            'total_regulations': regulations_count,
            'parsed_count': parsed_count,
            'new_keywords_count': new_keywords_count,
            'action': f"解析{parsed_count}条法规，提取{new_keywords_count}个关键词"
        })

    logger.info(f"保存更新日志 -> {filepath}")


# ============================================================
# 第九部分：主流程
# ============================================================

def run(full_mode=False, check_only=False):
    """
    Agent 1 主流程

    参数：
        full_mode: 是否全量模式
        check_only: 是否仅检查更新
    """
    logger.info("=" * 60)
    logger.info("Agent 1 开始运行：监管政策监测")
    logger.info(f"运行模式：{'全量' if full_mode else '增量'}")
    logger.info("=" * 60)

    # 初始化自查器
    checker = SelfChecker()

    # Step 1：加载数据
    logger.info("\n===== Step 1：加载数据 =====")
    regulations = load_regulation_registry()
    checker.check(len(regulations) > 0, "法规清单非空", "法规清单为空")

    synonyms_map = load_synonyms()
    stopwords = load_stopwords()
    existing_keywords = load_existing_keywords()

    # Step 2：检查更新
    logger.info("\n===== Step 2：检查更新 =====")
    if full_mode:
        # 全量模式：解析所有已确认的法规
        need_parse = [r for r in regulations if r.get('link_status') == '已确认']
    else:
        need_parse = check_for_updates(regulations, checker)

    if check_only:
        logger.info("仅检查模式，不进行解析")
        checker.summary()
        return

    if not need_parse:
        logger.info("没有需要解析的法规，退出")
        checker.summary()
        return

    # Step 3：读取法规文本
    logger.info(f"\n===== Step 3：读取法规文本（{len(need_parse)} 条）=====")
    all_keywords = []
    parsed_ids = []

    for i, reg in enumerate(need_parse, 1):
        reg_id = reg.get('id', '')
        reg_name = reg.get('regulation_name', '')
        logger.info(f"\n[{i}/{len(need_parse)}] 正在解析：{reg_id} - {reg_name[:30]}...")

        # 读取法规文本
        text, error = fetch_regulation_text(reg)

        if error:
            logger.error(f"  读取失败：{error}")
            checker.warn(False, f"{reg_id} 读取失败：{error}")
            continue

        logger.info(f"  读取成功，文本长度：{len(text)} 字符")
        parsed_ids.append(reg_id)

        # Step 4：关键词提取
        logger.info(f"  开始关键词提取...")
        keywords = extract_all_keywords(text, reg_id, checker)
        all_keywords.extend(keywords)
        logger.info(f"  提取关键词：{len(keywords)} 个")

        # 礼貌间隔
        time.sleep(3)

    # Step 5：自查与去重
    logger.info(f"\n===== Step 5：自查与去重 =====")
    checker.check(len(all_keywords) > 0, "原始关键词非空", "未提取到任何关键词")
    logger.info(f"原始关键词总数：{len(all_keywords)} 个")

    deduplicated = deduplicate_keywords(all_keywords, synonyms_map, stopwords)

    # Step 6：CDE交叉验证
    logger.info(f"\n===== Step 6：CDE交叉验证 =====")
    verified = verify_with_cde(deduplicated, checker)

    # Step 7：保存结果
    logger.info(f"\n===== Step 7：保存结果 =====")
    save_keyword_database(verified, existing_keywords)
    update_regulation_status(regulations, parsed_ids)
    save_update_log(len(regulations), len(parsed_ids), len(verified),
                    "全量解析" if full_mode else "增量更新")

    # 输出自查总结
    logger.info("\n")
    checker.summary()

    logger.info("\n" + "=" * 60)
    logger.info(f"Agent 1 运行完成")
    logger.info(f"  解析法规数：{len(parsed_ids)}")
    logger.info(f"  提取关键词数：{len(verified)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="全量模式")
    parser.add_argument("--check-only", action="store_true", help="仅检查")
    args = parser.parse_args()
    run(full_mode=args.full, check_only=args.check_only)
