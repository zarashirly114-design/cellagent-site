# CellAgent — 细胞治疗行业代理商招募平台

## 项目定位
中国首个细胞治疗行业代理商招募撮合平台，连接细胞治疗企业（甲方）与医药代理商（乙方），解决双方信息不对称问题。

## 产品名称
CellAgent（细胞代理通）

## 技术栈
- Python 3.13+
- 数据采集：Playwright
- 数据存储：CSV（数据层），SQLite（应用层）
- 后端：Flask
- 部署：ngrok（测试），云服务器（正式）

## 项目结构


cell-agent-platform/ ├── agents/ # 数据采集Agent │ ├── agent_0_company_v2.py # Agent 0：企业清单采集（CDE + NMPA） │ └── agent_1_regulation.py # Agent 1：监管政策监测 ├── data/ # 数据文件 │ ├── cell_companies.csv # 67家企业清单（核心数据） │ ├── keyword_database.csv # 1040个关键词库 │ ├── regulation_registry.csv # 55条监管政策记录 │ ├── cell_domain_dict.txt # 专业词典 │ ├── stopwords.csv # 停用词 │ └── synonyms.csv # 同义词 ├── utils/ # 工具模块 │ ├── logger.py # 日志工具 │ └── validators.py # 验证工具 ├── research/ # 调研与验证 │ ├── 项目日志001.html # 项目日志（可分享） │ └── 调研结果.json # 需求调研数据 ├── templates/ # 前端模板（待开发） ├── logs/ # 日志文件 ├── run.py # Agent运行入口 ├── landing.py # MVP落地页（Flask应用） ├── requirements.txt # Python依赖 ├── README.md # 项目说明 ├── CLAUDE.md # AI助手配置（本文件） └── .gitignore # Git忽略规则

## 代码运行顺序

### 1. Agent 0：企业清单采集

```bash
# 采集CDE和NMPA数据（约15分钟）
python3 run.py --agent 0 --sources CDE NMPA --years 2026 2025

注意：Agent 0 中的 NMPA 数据为硬编码（NMPA官网有反爬机制HTTP 412），如需更新需手动修改 collect_nmpa_data() 函数。
 
2. Agent 1：监管政策监测
# 检查监管更新
python3 run.py --agent 1 --check-only

# 全量采集
python3 run.py --agent 1 --full

3. MVP落地页
# 启动落地页（端口5001）
python3 landing.py

# 浏览器访问
# 注册页面：http://localhost:5001
# 数据后台：http://localhost:5001/admin/results

# 部署到公网（需要另一个终端窗口）
ngrok http 5001

数据源
 
数据源	类型	数据量	采集方式
CDE药审中心	在研产品企业	60家	Playwright自动采集
NMPA国家药监局	已获批产品	8款	硬编码（手动更新）
国家卫健委	干细胞备案机构	20家	硬编码（手动更新）
卫健委批准	脐带血库	7家	硬编码（手动更新）
企业信息	细胞存储/制备企业	10+家	硬编码（手动更新）
药监局	细胞检测机构	8家	硬编码（手动更新）
招聘网站	企业招聘信号	45条	浏览器搜索（验证用）
 
用户角色
 
甲方：细胞治疗企业（招代理商），如复星凯特、药明巨诺、科济药业
乙方：医药代理商/经销商（找产品代理），如医药商业公司、区域经销商
可代理产品清单（15个）
 
已获批药品（8款）
CAR-T（6款）：奕凯达（复星凯特）、倍诺达（药明巨诺）、福可苏（科济药业）、源瑞达（合源生物）、赛恺泽（科济药业）、卡卫荻（传奇生物）
干细胞药品（1款）：睿铂生（铂生卓越）
TIL（1款）：GC203（君赛生物）
 
细胞存储服务（7家）
上海细胞治疗集团、深圳泽医、北科生物、中源协和、博雅干细胞、汉氏联合、南华生物

验证状态
 
✅ 供给端验证：7/7已获批企业有销售/商务岗位招聘
⏳ 需求端验证：落地页已上线，等待投放测试
⏳ 企业入驻：待联系
⏳ 第一单撮合：待完成
 
代码规范
所有Agent必须包含自查和交叉验证机制
每条数据必须标注来源URL和采集日期
品类验证采用至少两个独立信号原则
仑赛类关键词必须额外验证是否为细胞产品
严格医疗级和生物级细胞产品，排除植物干细胞护肤品
NMPA数据更新需手动修改 collect_nmpa_data() 函数
落地页数据库 data/landing.db 不提交Git
 
待开发功能
 
Agent A：招商清单采集（调整为企业自填）
Agent B：需求端采集（调整为代理商注册时填写）
Agent C：供需匹配（初期用简单搜索替代）
完整MVP：企业后台、代理商后台、申请审核流程 EOF

