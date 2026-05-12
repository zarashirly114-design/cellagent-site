"""
细胞行业代理商招募平台 - Agent运行工具
"""

import argparse
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def main():
    parser = argparse.ArgumentParser(description="细胞行业代理商招募平台 - Agent运行工具")
    parser.add_argument("--agent", required=True, choices=['0', '1', 'a', 'b', 'c', 'all'],
                        help="指定运行的Agent（0=企业采集, 1=监管监测, a=招商采集, b=需求端, c=匹配, all=全部）")
    parser.add_argument("--full", action="store_true", help="全量模式")
    parser.add_argument("--check-only", action="store_true", help="仅检查更新")
    parser.add_argument("--sources", nargs='+', default=None,
                        help="数据源列表（Agent 0专用，如：CDE NMPA）")
    parser.add_argument("--keywords", nargs='+', default=None,
                        help="搜索关键词（Agent 0专用，如：CAR-T 干细胞）")
    parser.add_argument("--years", nargs='+', default=None,
                        help="年份范围（Agent 0专用，如：2026 2025 2024）")

    args = parser.parse_args()

    print("=" * 60)
    print("细胞行业代理商招募平台 - Agent运行工具")
    print("=" * 60)

    if args.agent in ['0', 'all']:
        print("\n>>> 运行 Agent 0：细胞企业清单采集")
        from agents.agent_0_company_v2 import run as run_agent_0
        run_agent_0(keywords=args.keywords, sources=args.sources, years=args.years)

    if args.agent in ['1', 'all']:
        print("\n>>> 运行 Agent 1：监管政策监测")
        from agents.agent_1_regulation import run as run_agent_1
        run_agent_1(full_mode=args.full, check_only=args.check_only)

    if args.agent in ['a', 'all']:
        print("\n>>> Agent A：招商清单采集 - 功能开发中")

    if args.agent in ['b', 'all']:
        print("\n>>> Agent B：需求端采集 - 功能开发中")

    if args.agent in ['c', 'all']:
        print("\n>>> Agent C：供需匹配 - 功能开发中")

    print("\n" + "=" * 60)
    print("运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
