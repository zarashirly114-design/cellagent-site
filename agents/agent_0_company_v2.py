"""
Agent 0：细胞企业清单采集Agent v2.2
修复：增加每页条数、使用药品类型筛选、增加提取页数
"""

import csv
import os
import re
import sys
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import get_agent_logger

logger = get_agent_logger("agent_0")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


# ============================================================
# 第一部分：CDE数据采集
# ============================================================

def get_cde_page_configs():
    """获取CDE各页面配置"""
    return {
        '受理品种信息': {
            'url': 'https://www.cde.org.cn/main/xxgk/listpage/9f9c74c73e0f8f56a8bfbc646055026d',
            'company_col_names': ['企业名称'],
            'product_col_names': ['药品名称'],
            'accept_col_names': ['受理号'],
            'has_drug_type_filter': True,
        },
        '优先审评公示': {
            'url': 'https://www.cde.org.cn/main/xxgk/listpage/2f78f372d351c6851af7431c7710a731',
            'company_col_names': ['注册申请人', '企业名称'],
            'product_col_names': ['药品名称'],
            'accept_col_names': ['受理号'],
            'has_drug_type_filter': False,
        },
        '突破性治疗公示': {
            'url': 'https://www.cde.org.cn/main/xxgk/listpage/da6efd086c099b7fc949121166f0130c',
            'company_col_names': ['注册申请人', '企业名称'],
            'product_col_names': ['药品名称'],
            'accept_col_names': ['受理号'],
            'has_drug_type_filter': False,
        },
        '临床试验默示许可': {
            'url': 'https://www.cde.org.cn/main/xxgk/listpage/4b5255eb0a84820cef4ca3e8b6bbe20c',
            'company_col_names': ['申请人名称', '注册申请人', '企业名称'],
            'product_col_names': ['药品名称'],
            'accept_col_names': ['受理号'],
            'has_drug_type_filter': False,
        },
        '上市药品信息': {
            'url': 'https://www.cde.org.cn/main/xxgk/listpage/b40868b5e21c038a6aa8b4319d21b07d',
            'company_col_names': ['企业名称'],
            'product_col_names': ['药品名称'],
            'accept_col_names': ['受理号'],
            'has_drug_type_filter': True,
        },
    }


def find_column_index(headers, target_names):
    """在表头中查找目标列的索引"""
    for i, header in enumerate(headers):
        header_clean = header.strip()
        for target in target_names:
            if target in header_clean:
                return i
    return -1


def set_per_page_50(page):
    """设置每页显示50条"""
    try:
        # 查找每页条数的下拉框
        selects = page.query_selector_all('select')
        for sel in selects:
            options = sel.query_selector_all('option')
            for opt in options:
                val = opt.get_attribute('value') or ''
                text = opt.text_content().strip()
                if '50' in text or val == '50':
                    sel.select_option(val)
                    time.sleep(3)
                    logger.info(f"  设置每页显示：{text}")
                    return True
    except Exception as e:
        logger.debug(f"  设置每页条数失败：{e}")
    return False


def set_drug_type_filter(page, drug_type='治疗用生物制品'):
    """设置药品类型筛选"""
    try:
        drug_type_select = page.query_selector('select[name="drugtype"]')
        if drug_type_select and drug_type_select.is_visible():
            # 查找匹配的选项
            options = drug_type_select.query_selector_all('option')
            for opt in options:
                text = opt.text_content().strip()
                val = opt.get_attribute('value') or ''
                if drug_type in text or drug_type in val:
                    drug_type_select.select_option(val)
                    time.sleep(2)
                    logger.info(f"  设置药品类型：{text}")

                    # 点击查询按钮
                    query_btn = page.query_selector('button:has-text("查询")')
                    if query_btn and query_btn.is_visible():
                        query_btn.click()
                        time.sleep(3)
                    return True
    except Exception as e:
        logger.debug(f"  设置药品类型筛选失败：{e}")
    return False


def get_total_pages(page):
    """获取总页数"""
    try:
        page_info = page.query_selector('.layui-laypage')
        if page_info:
            text = page_info.text_content()
            # 提取总条数
            match = re.search(r'共\s*(\d+)\s*条', text)
            if match:
                total = int(match.group(1))
                per_page = 50  # 假设已设置为50条/页
                total_pages = (total + per_page - 1) // per_page
                return total, total_pages
    except:
        pass
    return 0, 0


def extract_cde_page_data(page, page_name, page_config, keywords, max_pages=10):
    """
    从CDE页面提取数据
    动态识别表格结构，根据表头确定列位置
    """
    logger.info(f"  提取{page_name}数据...")

    all_results = []

    try:
        # 等待页面加载
        time.sleep(5)

        # 查找可见的表格
        tables = page.query_selector_all('table')
        visible_table = None

        for table in tables:
            if table.is_visible():
                visible_table = table
                break

        if not visible_table:
            logger.warning(f"  未找到可见表格")
            return []

        # 获取表头
        header_cells = visible_table.query_selector_all('thead th, thead td')
        headers = [cell.text_content().strip() for cell in header_cells]
        logger.info(f"  表头：{headers}")

        # 动态查找列索引
        company_col_idx = find_column_index(headers, page_config['company_col_names'])
        product_col_idx = find_column_index(headers, page_config['product_col_names'])
        accept_col_idx = find_column_index(headers, page_config['accept_col_names'])

        logger.info(f"  企业名称列：{company_col_idx}, 药品名称列：{product_col_idx}, 受理号列：{accept_col_idx}")

        if company_col_idx == -1:
            logger.warning(f"  未找到企业名称列，跳过此页面")
            return []

        # 获取总页数
        total_records, total_pages = get_total_pages(page)
        actual_max_pages = min(max_pages, total_pages) if total_pages > 0 else max_pages
        logger.info(f"  总记录数：{total_records}, 总页数：{total_pages}, 最大提取页数：{actual_max_pages}")

        # 遍历页面
        page_num = 1
        while page_num <= actual_max_pages:
            logger.info(f"  提取第{page_num}页...")

            # 提取当前页数据
            rows = visible_table.query_selector_all('tbody tr')

            page_count = 0
            for row in rows:
                cells = row.query_selector_all('td')
                if len(cells) <= company_col_idx:
                    continue

                # 动态提取数据
                company_name = cells[company_col_idx].text_content().strip()
                product_name = cells[product_col_idx].text_content().strip() if product_col_idx >= 0 and product_col_idx < len(cells) else ''
                accept_no = cells[accept_col_idx].text_content().strip() if accept_col_idx >= 0 and accept_col_idx < len(cells) else ''

                # 检查是否包含关键词
                row_text = f"{company_name} {product_name}".lower()
                if any(keyword.lower() in row_text for keyword in keywords):
                    all_results.append({
                        '企业名称': company_name,
                        '药品名称': product_name,
                        '受理号': accept_no,
                        '数据来源': f'CDE-{page_name}',
                        '搜索日期': datetime.now().strftime('%Y-%m-%d')
                    })
                    page_count += 1

            logger.info(f"  第{page_num}页提取：{page_count}条细胞相关记录")

            # 翻页
            try:
                next_btn = page.query_selector('.layui-laypage-next')
                if next_btn and 'disabled' not in (next_btn.get_attribute('class') or ''):
                    next_btn.click()
                    time.sleep(3)

                    # 重新获取表格引用
                    tables = page.query_selector_all('table')
                    for table in tables:
                        if table.is_visible():
                            visible_table = table
                            break

                    page_num += 1
                else:
                    break
            except Exception as e:
                logger.error(f"  翻页失败：{e}")
                break

        logger.info(f"  {page_name}提取完成：共{len(all_results)}条")
        return all_results

    except Exception as e:
        logger.error(f"  {page_name}提取失败：{e}")
        return []


def set_cde_year_filter(page, year):
    """设置CDE年份筛选"""
    try:
        year_select = page.query_selector('select[name="year"]')
        if year_select and year_select.is_visible():
            year_select.select_option(str(year))
            time.sleep(2)

            query_btn = page.query_selector('button:has-text("查询")')
            if query_btn and query_btn.is_visible():
                query_btn.click()
                time.sleep(3)

            return True
    except Exception as e:
        logger.debug(f"  设置年份筛选失败：{e}")
    return False


def collect_cde_data(keywords, years):
    """从CDE采集数据"""
    logger.info("开始CDE数据采集...")

    page_configs = get_cde_page_configs()
    all_results = []

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
            )

            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1440, "height": 900},
                locale="zh-CN",
            )

            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

            for page_name, page_config in page_configs.items():
                logger.info(f"\n--- 采集{page_name} ---")

                try:
                    page.goto(page_config['url'], timeout=60000)
                    time.sleep(8)

                    # 设置每页显示50条
                    set_per_page_50(page)

                    # 如果有药品类型筛选，设置为"治疗用生物制品"
                    if page_config.get('has_drug_type_filter'):
                        set_drug_type_filter(page, '治疗用生物制品')

                    # 提取默认数据
                    results = extract_cde_page_data(page, page_name, page_config, keywords, max_pages=20)
                    all_results.extend(results)

                    # 遍历年份
                    for year in years:
                        logger.info(f"  设置年份：{year}")
                        if set_cde_year_filter(page, year):
                            # 重新设置每页50条
                            set_per_page_50(page)
                            # 重新设置药品类型筛选
                            if page_config.get('has_drug_type_filter'):
                                set_drug_type_filter(page, '治疗用生物制品')

                            results = extract_cde_page_data(page, page_name, page_config, keywords, max_pages=20)
                            all_results.extend(results)

                    logger.info(f"  {page_name}采集完成")

                except Exception as e:
                    logger.error(f"  {page_name}采集失败：{e}")

                time.sleep(3)

            browser.close()

    except Exception as e:
        logger.error(f"CDE数据采集失败：{e}")

    return all_results


# ============================================================
# 第二部分：数据合并与去重
# ============================================================




# ============================================================
# NMPA数据采集
# ============================================================

def collect_nmpa_data():
    """从NMPA采集数据（基于公开信息整理）"""
    logger.info('开始NMPA数据采集...')
    logger.info('  NMPA官网有反自动化检测(HTTP 412)，使用硬编码数据')

    nmpa_products = [
        {'company': '复星凯特', 'product': '阿基仑赛注射液（奕凯达）', 'type': 'CAR-T', 'year': 2021},
        {'company': '药明巨诺', 'product': '瑞基奥仑赛注射液（倍诺达）', 'type': 'CAR-T', 'year': 2021},
        {'company': '科济药业', 'product': '伊基奥仑赛注射液（福可苏）', 'type': 'CAR-T', 'year': 2023},
        {'company': '合源生物', 'product': '纳基奥仑赛注射液（源瑞达）', 'type': 'CAR-T', 'year': 2023},
        {'company': '科济药业', 'product': '泽沃基奥仑赛注射液（赛恺泽）', 'type': 'CAR-T', 'year': 2024},
        {'company': '传奇生物', 'product': '西达基奥仑赛注射液（卡卫荻）', 'type': 'CAR-T', 'year': 2024},
        {'company': '铂生卓越生物', 'product': '艾米迈托赛注射液（睿铂生）', 'type': '干细胞', 'year': 2025},
        {'company': '上海君赛生物', 'product': 'GC203 TIL细胞注射液', 'type': 'TIL', 'year': 2024},
    ]

    results = []
    for item in nmpa_products:
        results.append({
            '企业名称': item['company'],
            '产品信息': item['product'],
            '产品类型': item['type'],
            '获批年份': item['year'],
            '受理号': '',
            '数据来源': 'NMPA已获批产品',
            '搜索日期': datetime.now().strftime('%Y-%m-%d')
        })

    logger.info(f'  NMPA采集完成：{len(results)} 条')
    return results


def merge_and_deduplicate(all_results):
    """合并所有数据源的结果并去重"""
    logger.info(f"合并前总数：{len(all_results)} 条")

    seen = set()
    unique_results = []

    for result in all_results:
        company = result.get('企业名称', '').strip()
        product = result.get('药品名称', '').strip()

        if not company:
            continue

        companies = [c.strip() for c in company.split(';') if c.strip() and c.strip() != '----']

        for comp in companies:
            key = f"{comp}|{product}"
            if key not in seen:
                seen.add(key)
                unique_results.append({
                    '企业名称': comp,
                    '药品名称': product,
                    '受理号': result.get('受理号', ''),
                    '数据来源': result.get('数据来源', ''),
                    '搜索日期': result.get('搜索日期', '')
                })

    company_map = {}
    for result in unique_results:
        company = result['企业名称']
        if company not in company_map:
            company_map[company] = {
                '企业名称': company,
                '数据来源': set(),
                '产品信息': set(),
                '受理号': set(),
            }

        company_map[company]['数据来源'].add(result['数据来源'])
        if result['药品名称']:
            company_map[company]['产品信息'].add(result['药品名称'])
        if result['受理号'] and result['受理号'] != '无':
            company_map[company]['受理号'].add(result['受理号'])

    merged_results = []
    for company_name, info in company_map.items():
        merged_results.append({
            '企业名称': company_name,
            '数据来源': ';'.join(sorted(info['数据来源'])),
            '产品信息': ';'.join(list(info['产品信息'])[:5]),
            '受理号': ';'.join(list(info['受理号'])[:5]),
            '搜索日期': datetime.now().strftime('%Y-%m-%d')
        })

    logger.info(f"去重后总数：{len(merged_results)} 条")
    return merged_results


# ============================================================
# 第三部分：保存结果
# ============================================================

def save_to_csv(results, filename="cell_companies.csv"):
    """保存结果到CSV文件"""
    filepath = os.path.join(DATA_DIR, filename)

    fieldnames = [
        'id', '企业名称', '统一社会信用代码', '所在地区', '主营业务',
        '产品信息', '受理号', '数据来源', '来源URL', '验证状态',
        '创建日期', '备注'
    ]

    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for i, result in enumerate(results, 1):
            row = {
                'id': f"COM-{i:04d}",
                '企业名称': result.get('企业名称', ''),
                '统一社会信用代码': '',
                '所在地区': '',
                '主营业务': '',
                '产品信息': result.get('产品信息', ''),
                '受理号': result.get('受理号', ''),
                '数据来源': result.get('数据来源', ''),
                '来源URL': '',
                '验证状态': '待验证',
                '创建日期': datetime.now().strftime('%Y-%m-%d'),
                '备注': ''
            }
            writer.writerow(row)

    logger.info(f"保存企业清单：{len(results)} 条 -> {filepath}")
    return filepath


# ============================================================
# 第四部分：主流程
# ============================================================

def run(keywords=None, sources=None, years=None):
    """Agent 0 主流程"""
    logger.info("=" * 60)
    logger.info("Agent 0 开始运行：细胞企业清单采集 v2.2")
    logger.info("=" * 60)

    if keywords is None:
        keywords = [
            '细胞', 'CAR-T', 'CAR-NK', 'TCR-T', 'TIL',
            '干细胞', '间充质', '造血干',
            '免疫细胞', 'NK细胞', 'DC细胞',
            '细胞治疗', '细胞产品', '细胞制剂',
            '基因治疗', '基因编辑', '外泌体'
        ]

    if sources is None:
        sources = ['CDE']

    if years is None:
        years = ['2026', '2025', '2024']

    logger.info(f"搜索关键词：{keywords}")
    logger.info(f"数据源：{sources}")
    logger.info(f"年份范围：{years}")

    all_results = []

    if 'CDE' in sources:
        logger.info("\n===== CDE数据采集 =====")
        cde_results = collect_cde_data(keywords, years)
        all_results.extend(cde_results)
        logger.info(f"  CDE采集完成：{len(cde_results)} 条")

    logger.info("\n===== 合并与去重 =====")
    merged_results = merge_and_deduplicate(all_results)

    logger.info("\n===== 保存结果 =====")
    save_to_csv(merged_results)

    logger.info("\n" + "=" * 60)
    logger.info("Agent 0 运行完成")
    logger.info(f"  采集企业数：{len(merged_results)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords", nargs='+', help="搜索关键词")
    parser.add_argument("--sources", nargs='+', help="数据源列表", default=['CDE'])
    parser.add_argument("--years", nargs='+', help="年份列表", default=['2026', '2025', '2024'])
    args = parser.parse_args()

    run(keywords=args.keywords, sources=args.sources, years=args.years)
