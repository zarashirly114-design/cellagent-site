"""
真正的调研：用浏览器搜索验证需求
"""

import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright


def search_with_browser(page, keyword):
    """用百度搜索并提取结果"""
    print(f"\n搜索：{keyword}")
    print("-" * 50)

    try:
        encoded = keyword.replace(' ', '+')
        page.goto(f'https://www.baidu.com/s?wd={encoded}', timeout=30000)
        time.sleep(3)

        # 提取搜索结果
        results = []
        items = page.query_selector_all('.result, .c-container')

        for i, item in enumerate(items[:8]):
            try:
                title_el = item.query_selector('h3 a, .t a')
                abstract_el = item.query_selector('.content-right_8Zs40, .c-abstract, .c-span-last')

                title = title_el.text_content().strip() if title_el else ""
                abstract = abstract_el.text_content().strip()[:100] if abstract_el else ""
                href = title_el.get_attribute('href') if title_el else ""

                if title and len(title) > 5:
                    results.append({
                        "title": title[:80],
                        "abstract": abstract,
                        "url": href
                    })
                    print(f"  {len(results)}. {title[:60]}")
                    if abstract:
                        print(f"     {abstract[:50]}...")
            except:
                continue

        print(f"  共找到 {len(results)} 条结果")
        return results

    except Exception as e:
        print(f"  搜索失败：{e}")
        return []


def run_research():
    """执行调研"""
    print("=" * 60)
    print("CellAgent 需求验证调研（浏览器搜索）")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    all_results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

        # ============================================================
        # 调研1：企业是否有招商需求
        # ============================================================
        print("\n\n" + "=" * 60)
        print("【调研1】企业招商需求验证")
        print("核心问题：细胞治疗企业是否在找代理商？")
        print("=" * 60)

        recruitment_keywords = [
            "CAR-T 招代理商",
            "细胞治疗 代理加盟",
            "干细胞产品 招商合作",
            "CAR-T 区域代理 招募",
        ]

        recruitment_results = []
        for kw in recruitment_keywords:
            results = search_with_browser(page, kw)
            recruitment_results.extend(results)
            time.sleep(2)

        all_results["企业招商需求"] = {
            "搜索词": recruitment_keywords,
            "结果数": len(recruitment_results),
            "结果": recruitment_results
        }

        # ============================================================
        # 调研2：代理商是否有需求
        # ============================================================
        print("\n\n" + "=" * 60)
        print("【调研2】代理商需求验证")
        print("核心问题：代理商是否想找细胞治疗产品？")
        print("=" * 60)

        agent_keywords = [
            "想做细胞治疗产品代理",
            "CAR-T代理 怎么做",
            "医药代理 转型 细胞治疗",
            "找干细胞产品 代理",
        ]

        agent_results = []
        for kw in agent_keywords:
            results = search_with_browser(page, kw)
            agent_results.extend(results)
            time.sleep(2)

        all_results["代理商需求"] = {
            "搜索词": agent_keywords,
            "结果数": len(agent_results),
            "结果": agent_results
        }

        # ============================================================
        # 调研3：竞品调研
        # ============================================================
        print("\n\n" + "=" * 60)
        print("【调研3】竞品调研")
        print("核心问题：有没有类似平台已经存在？")
        print("=" * 60)

        competitor_keywords = [
            "细胞治疗 招商平台",
            "医药代理商 对接平台",
            "细胞治疗 行业数据平台",
        ]

        competitor_results = []
        for kw in competitor_keywords:
            results = search_with_browser(page, kw)
            competitor_results.extend(results)
            time.sleep(2)

        all_results["竞品调研"] = {
            "搜索词": competitor_keywords,
            "结果数": len(competitor_results),
            "结果": competitor_results
        }

        # ============================================================
        # 调研4：企业官网验证
        # ============================================================
        print("\n\n" + "=" * 60)
        print("【调研4】企业官网验证")
        print("核心问题：已获批企业官网是否有招商/合作入口？")
        print("=" * 60)

        company_sites = [
            {"name": "复星凯特", "url": "https://www.fosunkite.com"},
            {"name": "药明巨诺", "url": "https://www.juventas.com"},
            {"name": "科济药业", "url": "https://www.carsgen.com"},
            {"name": "合源生物", "url": "https://www.henogen.com"},
            {"name": "传奇生物", "url": "https://www.legendbiotech.com"},
        ]

        company_results = []
        for company in company_sites:
            print(f"\n检查：{company['name']} ({company['url']})")
            try:
                page.goto(company['url'], timeout=15000)
                time.sleep(2)

                content = page.content()

                has_recruit = any(kw in content for kw in ['招商', '代理', '经销', '合作', '加盟'])
                has_contact = any(kw in content for kw in ['联系', '电话', '邮箱', 'contact'])

                result = {
                    "企业": company['name'],
                    "网址": company['url'],
                    "有招商入口": has_recruit,
                    "有联系方式": has_contact,
                }
                company_results.append(result)

                status = "✅ 有招商/合作入口" if has_recruit else "❌ 未发现招商入口"
                print(f"  {status}")

            except Exception as e:
                print(f"  访问失败：{e}")
                company_results.append({
                    "企业": company['name'],
                    "网址": company['url'],
                    "有招商入口": "无法访问",
                    "有联系方式": "无法访问",
                })

        all_results["企业官网验证"] = company_results

        browser.close()

    # ============================================================
    # 保存结果
    # ============================================================
    output_file = "research/调研结果_真实数据.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    # ============================================================
    # 输出结论
    # ============================================================
    print("\n\n" + "=" * 60)
    print("调研数据汇总")
    print("=" * 60)

    print(f"\n1. 企业招商需求搜索：{len(recruitment_results)} 条结果")
    for r in recruitment_results[:5]:
        print(f"   - {r['title'][:50]}")

    print(f"\n2. 代理商需求搜索：{len(agent_results)} 条结果")
    for r in agent_results[:5]:
        print(f"   - {r['title'][:50]}")

    print(f"\n3. 竞品搜索：{len(competitor_results)} 条结果")
    for r in competitor_results[:5]:
        print(f"   - {r['title'][:50]}")

    print(f"\n4. 企业官网验证：")
    for r in company_results:
        status = "✅" if r.get("有招商入口") else "❌"
        print(f"   {status} {r['企业']}")

    # 结论
    print("\n\n" + "=" * 60)
    print("调研结论")
    print("=" * 60)

    recruit_count = len(recruitment_results)
    agent_count = len(agent_results)
    competitor_count = len(competitor_results)
    company_with_recruit = sum(1 for r in company_results if r.get("有招商入口"))

    print(f"""
数据指标：
├── 企业招商搜索结果：{recruit_count} 条
├── 代理商需求搜索结果：{agent_count} 条
├── 竞品搜索结果：{competitor_count} 条
└── 企业官网有招商入口：{company_with_recruit}/{len(company_results)} 家
    """)

    if recruit_count >= 10 and agent_count >= 5:
        print("结论：✅ 需求验证通过，两端需求都存在")
        print("建议：继续开发MVP")
    elif recruit_count >= 5 or agent_count >= 3:
        print("结论：⚠️ 部分验证，需求存在但需要进一步确认")
        print("建议：先做落地页测试注册意愿")
    else:
        print("结论：❌ 需求证据不足")
        print("建议：需要深入调研，或调整产品方向")

    print(f"\n完整结果已保存到：{output_file}")


if __name__ == "__main__":
    run_research()
