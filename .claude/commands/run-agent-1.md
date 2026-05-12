运行以下命令执行Agent 1，采集法规并提取关键词：

cd /Users/apple/cell-agent-platform && python3 run.py --agent 1

首次运行：全量解析所有法规，生成完整关键词库
后续运行：增量更新，只解析变化的法规

输出文件：
- data/keyword_database.csv（关键词词库）
- data/update_log.csv（更新日志）
- data/regulation_registry.csv（更新法规清单状态）

运行前请确保已安装依赖：pip3 install -r requirements.txt
