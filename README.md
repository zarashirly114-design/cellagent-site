# 细胞行业代理商招募平台

## 项目概述

细胞行业企业数据采集与分析平台，用于构建细胞行业代理商网络。

## 数据源

| 数据源 | 类型 | 企业数 |
|---|---|---|
| CDE | 在研产品企业 | 60+ |
| NMPA | 已获批产品企业 | 8 |
| 卫健委 | 干细胞临床研究备案机构 | 20 |
| 卫健委 | 脐带血造血干细胞库 | 7 |
| 企业信息 | 细胞存储/制备机构 | 10+ |
| 药监局 | 细胞检测机构 | 8 |

## 文件结构


cell-agent-platform/ ├── agents/ # Agent模块 │ ├── agent_0_company_v2.py # 企业清单采集Agent │ └── agent_1_regulation.py # 监管政策监测Agent ├── data/ # 数据文件 │ ├── cell_companies.csv # 企业清单（67家） │ ├── regulation_registry.csv # 监管政策库 │ ├── keyword_database.csv # 关键词库 │ └── ... ├── utils/ # 工具模块 │ ├── logger.py # 日志工具 │ └── validators.py # 验证工具 ├── logs/ # 日志文件 ├── reports/ # 报告文件 ├── run.py # 主运行脚本 ├── requirements.txt # 依赖包 └── README.md # 项目说明

## 使用方法

### Agent 0：企业清单采集

```bash
# 采集CDE和NMPA数据
python3 run.py --agent 0 --sources CDE NMPA --years 2026 2025

Agent 1：监管政策监测
# 检查监管更新
python3 run.py --agent 1 --check-only

数据字段
 
cell_companies.csv
 
字段	说明
id	企业编号
企业名称	企业/机构名称
统一社会信用代码	待补充
所在地区	省/市
主营业务	细胞存储/制备/检测/临床研究
产品信息	在研/已上市产品
产品类型	CAR-T/干细胞/TIL等
获批年份	NMPA获批年份
受理号	CDE受理号
数据来源	CDE/NMPA/卫健委/药监局
验证状态	待验证/已验证
创建日期	采集日期
 
更新日志
 
2026-05-12
 
完成Agent 0 v3.1
整合CDE + NMPA + 卫健委 + 药监局数据
企业清单：67家
清理调试文件，整理项目文档
 
待办事项
 
 Agent A：招商清单采集
 Agent B：需求端数据采集
 Agent C：供需匹配
 网站开发
 数据验证与清洗
 
联系方式
 
待补充 EOF
 
echo "✅ README.md 已创建"
text
text

```bash
# 查看清理后的项目结构
tree -L 2 -a -I '__pycache__|*.pyc' 2>/dev/null || find . -maxdepth 2 -type f | grep -v __pycache__ | sort

