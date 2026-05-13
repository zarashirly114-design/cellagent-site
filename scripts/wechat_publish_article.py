"""
CellAgent 微信公众号文章发布
"""
import requests
import json
import os
import sys
import re

# ========== 加载.env ==========
def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    config = {}
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    return config

config = load_env()
APPID = config.get('WECHAT_APPID', '')
APPSECRET = config.get('WECHAT_APPSECRET', '')
BASE_URL = "https://zarashirly114-design.github.io/cellagent-site"

# ========== 获取access_token ==========
def get_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}"
    r = requests.get(url)
    data = r.json()
    return data.get("access_token")

# ========== 转换HTML为微信文章格式 ==========
def html_to_wechat_article(html_content):
    """将HTML转换为微信公众号支持的格式"""

    # 移除不需要的标签
    html_content = re.sub(r'<!DOCTYPE[^>]*>', '', html_content)
    html_content = re.sub(r'<html[^>]*>', '', html_content)
    html_content = re.sub(r'</html>', '', html_content)
    html_content = re.sub(r'<head[^>]*>.*?</head>', '', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<body[^>]*>', '', html_content)
    html_content = re.sub(r'</body>', '', html_content)
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)

    # 替换CSS变量为实际值
    replacements = {
        'var(--bg)': '#0a0f1a',
        'var(--surface)': '#111827',
        'var(--accent)': '#c9a84c',
        'var(--accent-light)': '#dbb960',
        'var(--green)': '#22c55e',
        'var(--blue)': '#3b82f6',
        'var(--red)': '#ef4444',
        'var(--purple)': '#a855f7',
        'var(--text)': '#f1f5f9',
        'var(--text-muted)': '#94a3b8',
        'var(--text-dim)': '#64748b',
        'var(--border)': 'rgba(255,255,255,0.08)',
    }
    for old, new in replacements.items():
        html_content = html_content.replace(old, new)

    return html_content

# ========== 生成公众号文章内容 ==========
def generate_article_content():
    """生成公众号文章HTML内容"""

    content = """
    <section style="max-width:100%;margin:0 auto;padding:20px;background:#0a0f1a;color:#f1f5f9;">

        <!-- 封面标题 -->
        <section style="text-align:center;padding:40px 0;">
            <h1 style="font-size:28px;font-weight:900;color:#c9a84c;margin-bottom:8px;">CellAgent</h1>
            <p style="font-size:14px;color:#94a3b8;letter-spacing:2px;">细 胞 代 理 通</p>
            <h2 style="font-size:24px;font-weight:700;color:#f1f5f9;margin-top:32px;line-height:1.5;">我们用一天时间<br>验证了一个商业想法</h2>
            <p style="font-size:13px;color:#64748b;margin-top:16px;">2026年5月12日 · 项目日志 #001</p>
        </section>

        <section style="width:40px;height:3px;background:#c9a84c;margin:30px auto;"></section>

        <!-- 痛点洞察 -->
        <section style="padding:20px 0;">
            <p style="font-size:11px;letter-spacing:3px;color:#c9a84c;margin-bottom:12px;">痛点洞察</p>
            <h2 style="font-size:22px;font-weight:700;color:#f1f5f9;margin-bottom:8px;">一个真实存在的问题</h2>
            <p style="font-size:14px;color:#94a3b8;margin-bottom:24px;">细胞治疗行业正在爆发，但企业与代理商之间存在严重的信息不对称。</p>

            <section style="border-left:3px solid #c9a84c;padding:12px 16px;background:rgba(201,168,76,0.05);margin:16px 0;">
                <p style="font-size:14px;color:#94a3b8;font-style:italic;">细胞治疗企业有产品，但不知道去哪里找代理商。<br>代理商想做细胞治疗，但不知道卖什么产品。</p>
            </section>

            <!-- 数据统计 -->
            <section style="display:flex;gap:12px;margin-top:24px;">
                <section style="flex:1;background:#111827;border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:16px;text-align:center;">
                    <p style="font-size:32px;font-weight:900;color:#c9a84c;">8</p>
                    <p style="font-size:11px;color:#94a3b8;">已获批产品</p>
                </section>
                <section style="flex:1;background:#111827;border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:16px;text-align:center;">
                    <p style="font-size:32px;font-weight:900;color:#22c55e;">67</p>
                    <p style="font-size:11px;color:#94a3b8;">入库企业</p>
                </section>
                <section style="flex:1;background:#111827;border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:16px;text-align:center;">
                    <p style="font-size:32px;font-weight:900;color:#3b82f6;">0</p>
                    <p style="font-size:11px;color:#94a3b8;">对接平台</p>
                </section>
            </section>
        </section>

        <section style="width:40px;height:3px;background:#c9a84c;margin:30px auto;"></section>

        <!-- 今日成果 -->
        <section style="padding:20px 0;">
            <p style="font-size:11px;letter-spacing:3px;color:#c9a84c;margin-bottom:12px;">今日成果</p>
            <h2 style="font-size:22px;font-weight:700;color:#f1f5f9;margin-bottom:8px;">一天做了什么</h2>
            <p style="font-size:14px;color:#94a3b8;margin-bottom:24px;">从0到1，完成数据采集、产品设计、需求验证全链路。</p>

            <!-- 时间线 -->
            <section style="position:relative;padding-left:32px;">
                <section style="position:absolute;left:8px;top:0;bottom:0;width:2px;background:linear-gradient(to bottom,#c9a84c,#22c55e,#3b82f6);"></section>

                <section style="position:relative;margin-bottom:24px;padding:16px;background:#111827;border-radius:12px;border:1px solid rgba(255,255,255,0.08);">
                    <section style="position:absolute;left:-28px;top:20px;width:12px;height:12px;border-radius:50%;background:#22c55e;border:3px solid #0a0f1a;"></section>
                    <p style="font-size:12px;color:#c9a84c;margin-bottom:4px;">上午 · 数据采集</p>
                    <p style="font-size:15px;font-weight:700;color:#f1f5f9;margin-bottom:6px;">Agent 0 自动化采集企业数据</p>
                    <p style="font-size:13px;color:#94a3b8;">从CDE、NMPA、卫健委等多个数据源，采集67家企业</p>
                </section>

                <section style="position:relative;margin-bottom:24px;padding:16px;background:#111827;border-radius:12px;border:1px solid rgba(255,255,255,0.08);">
                    <section style="position:absolute;left:-28px;top:20px;width:12px;height:12px;border-radius:50%;background:#22c55e;border:3px solid #0a0f1a;"></section>
                    <p style="font-size:12px;color:#c9a84c;margin-bottom:4px;">中午 · 数据合并</p>
                    <p style="font-size:15px;font-weight:700;color:#f1f5f9;margin-bottom:6px;">多源数据合并去重</p>
                    <p style="font-size:13px;color:#94a3b8;">CDE(60家)、NMPA(8款产品)、卫健委(27家机构)</p>
                </section>

                <section style="position:relative;margin-bottom:24px;padding:16px;background:#111827;border-radius:12px;border:1px solid rgba(255,255,255,0.08);">
                    <section style="position:absolute;left:-28px;top:20px;width:12px;height:12px;border-radius:50%;background:#22c55e;border:3px solid #0a0f1a;"></section>
                    <p style="font-size:12px;color:#c9a84c;margin-bottom:4px;">下午 · 产品设计</p>
                    <p style="font-size:15px;font-weight:700;color:#f1f5f9;margin-bottom:6px;">PRD文档 + 高保真原型</p>
                    <p style="font-size:13px;color:#94a3b8;">输出6个页面的高保真原型</p>
                </section>

                <section style="position:relative;margin-bottom:24px;padding:16px;background:#111827;border-radius:12px;border:1px solid rgba(255,255,255,0.08);">
                    <section style="position:absolute;left:-28px;top:20px;width:12px;height:12px;border-radius:50%;background:#22c55e;border:3px solid #0a0f1a;"></section>
                    <p style="font-size:12px;color:#c9a84c;margin-bottom:4px;">下午 · 需求验证</p>
                    <p style="font-size:15px;font-weight:700;color:#f1f5f9;margin-bottom:6px;">供给端验证：企业真的需要渠道</p>
                    <p style="font-size:13px;color:#94a3b8;">7/7已获批企业有销售岗位招聘</p>
                </section>

                <section style="position:relative;margin-bottom:24px;padding:16px;background:#111827;border-radius:12px;border:1px solid rgba(255,255,255,0.08);">
                    <section style="position:absolute;left:-28px;top:20px;width:12px;height:12px;border-radius:50%;background:#22c55e;border:3px solid #0a0f1a;"></section>
                    <p style="font-size:12px;color:#c9a84c;margin-bottom:4px;">晚上 · MVP上线</p>
                    <p style="font-size:15px;font-weight:700;color:#f1f5f9;margin-bottom:6px;">落地页部署到公网</p>
                    <p style="font-size:13px;color:#94a3b8;">支持手机访问和在线注册</p>
                </section>
            </section>
        </section>

        <section style="width:40px;height:3px;background:#c9a84c;margin:30px auto;"></section>

        <!-- 供给端验证 -->
        <section style="padding:20px 0;">
            <p style="font-size:11px;letter-spacing:3px;color:#c9a84c;margin-bottom:12px;">供给端验证</p>
            <h2 style="font-size:22px;font-weight:700;color:#f1f5f9;margin-bottom:8px;">企业真的在招人卖产品</h2>
            <p style="font-size:14px;color:#94a3b8;margin-bottom:24px;">7/7已获批企业都有销售/商务岗位在招。</p>

            <!-- 证据卡片 -->
            <section style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                <section style="background:#111827;border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:14px;text-align:center;">
                    <p style="font-size:14px;font-weight:700;color:#f1f5f9;">复星凯特</p>
                    <p style="font-size:12px;color:#22c55e;">销售经理</p>
                </section>
                <section style="background:#111827;border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:14px;text-align:center;">
                    <p style="font-size:14px;font-weight:700;color:#f1f5f9;">药明巨诺</p>
                    <p style="font-size:12px;color:#22c55e;">商务拓展经理</p>
                </section>
                <section style="background:#111827;border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:14px;text-align:center;">
                    <p style="font-size:14px;font-weight:700;color:#f1f5f9;">科济药业</p>
                    <p style="font-size:12px;color:#22c55e;">区域销售负责人</p>
                </section>
                <section style="background:#111827;border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:14px;text-align:center;">
                    <p style="font-size:14px;font-weight:700;color:#f1f5f9;">上海细胞治疗集团</p>
                    <p style="font-size:12px;color:#22c55e;">招商经理</p>
                </section>
            </section>

            <section style="border-left:3px solid #c9a84c;padding:12px 16px;background:rgba(201,168,76,0.05);margin:24px 0 0;">
                <p style="font-size:14px;color:#94a3b8;font-style:italic;">结论：企业需要渠道，需求100%真实</p>
            </section>
        </section>

        <section style="width:40px;height:3px;background:#c9a84c;margin:30px auto;"></section>

        <!-- 产品库 -->
        <section style="padding:20px 0;">
            <p style="font-size:11px;letter-spacing:3px;color:#c9a84c;margin-bottom:12px;">产品库</p>
            <h2 style="font-size:22px;font-weight:700;color:#f1f5f9;margin-bottom:8px;">15个可代理产品与服务</h2>
            <p style="font-size:14px;color:#94a3b8;margin-bottom:24px;">覆盖已获批药品和细胞存储服务。</p>

            <p style="font-size:13px;color:#c9a84c;margin-bottom:12px;font-weight:500;">已获批药品（8款）</p>

            <!-- 产品卡片 -->
            <section style="background:#111827;border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:14px;margin-bottom:12px;display:flex;align-items:center;gap:12px;">
                <section style="display:inline-block;padding:4px 10px;border-radius:4px;font-size:11px;font-weight:600;background:rgba(239,68,68,0.15);color:#f87171;">CAR-T</section>
                <section style="flex:1;">
                    <p style="font-size:14px;font-weight:500;color:#f1f5f9;">奕凯达</p>
                    <p style="font-size:12px;color:#64748b;">复星凯特 · 2021获批</p>
                </section>
            </section>

            <section style="background:#111827;border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:14px;margin-bottom:12px;display:flex;align-items:center;gap:12px;">
                <section style="display:inline-block;padding:4px 10px;border-radius:4px;font-size:11px;font-weight:600;background:rgba(239,68,68,0.15);color:#f87171;">CAR-T</section>
                <section style="flex:1;">
                    <p style="font-size:14px;font-weight:500;color:#f1f5f9;">倍诺达</p>
                    <p style="font-size:12px;color:#64748b;">药明巨诺 · 2021获批</p>
                </section>
            </section>

            <section style="background:#111827;border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:14px;margin-bottom:12px;display:flex;align-items:center;gap:12px;">
                <section style="display:inline-block;padding:4px 10px;border-radius:4px;font-size:11px;font-weight:600;background:rgba(168,85,247,0.15);color:#c084fc;">细胞存储</section>
                <section style="flex:1;">
                    <p style="font-size:14px;font-weight:500;color:#f1f5f9;">细胞存储服务</p>
                    <p style="font-size:12px;color:#64748b;">上海细胞治疗集团</p>
                </section>
            </section>

            <p style="font-size:12px;color:#94a3b8;text-align:center;margin-top:16px;">... 更多产品请访问平台查看</p>
        </section>

        <section style="width:40px;height:3px;background:#c9a84c;margin:30px auto;"></section>

        <!-- 验证进度 -->
        <section style="padding:20px 0;">
            <p style="font-size:11px;letter-spacing:3px;color:#c9a84c;margin-bottom:12px;">验证进度</p>
            <h2 style="font-size:22px;font-weight:700;color:#f1f5f9;margin-bottom:24px;">MVP验证清单</h2>

            <section style="display:flex;align-items:flex-start;gap:12px;padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.08);">
                <section style="width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;background:rgba(34,197,94,0.15);color:#22c55e;">✓</section>
                <section>
                    <p style="font-size:14px;color:#f1f5f9;">企业数据采集</p>
                    <p style="font-size:12px;color:#64748b;">67家企业，覆盖CDE、NMPA、卫健委</p>
                </section>
            </section>

            <section style="display:flex;align-items:flex-start;gap:12px;padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.08);">
                <section style="width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;background:rgba(34,197,94,0.15);color:#22c55e;">✓</section>
                <section>
                    <p style="font-size:14px;color:#f1f5f9;">供给端验证</p>
                    <p style="font-size:12px;color:#64748b;">7/7已获批企业有销售岗位招聘</p>
                </section>
            </section>

            <section style="display:flex;align-items:flex-start;gap:12px;padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.08);">
                <section style="width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;background:rgba(34,197,94,0.15);color:#22c55e;">✓</section>
                <section>
                    <p style="font-size:14px;color:#f1f5f9;">落地页上线</p>
                    <p style="font-size:12px;color:#64748b;">已部署公网，支持手机注册</p>
                </section>
            </section>

            <section style="display:flex;align-items:flex-start;gap:12px;padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.08);">
                <section style="width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;background:rgba(245,158,11,0.15);color:#f59e0b;">⏳</section>
                <section>
                    <p style="font-size:14px;color:#f1f5f9;">需求端验证</p>
                    <p style="font-size:12px;color:#64748b;">目标：2周内50人注册</p>
                </section>
            </section>
        </section>

        <section style="width:40px;height:3px;background:#c9a84c;margin:30px auto;"></section>

        <!-- CTA -->
        <section style="text-align:center;padding:30px 0;">
            <h2 style="font-size:22px;font-weight:700;color:#f1f5f9;margin-bottom:8px;">访问平台</h2>
            <p style="font-size:14px;color:#94a3b8;margin-bottom:24px;">查看完整产品原型和项目日志</p>
            <a href="https://zarashirly114-design.github.io/cellagent-site/" style="display:inline-block;padding:14px 32px;background:#c9a84c;color:#0a0f1a;border-radius:8px;font-size:15px;font-weight:700;text-decoration:none;">访问 CellAgent →</a>
            <p style="font-size:12px;color:#64748b;margin-top:32px;">项目日志 #001 · 2026年5月12日</p>
        </section>

    </section>
    """

    return content

# ========== 创建草稿 ==========
def create_draft(token, title, content, thumb_media_id):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    data = {
        "articles": [{
            "title": title,
            "author": "CellAgent",
            "content": content,
            "thumb_media_id": thumb_media_id,
            "content_source_url": BASE_URL,
            "need_open_comment": 1,
            "only_fans_can_comment": 0,
        }]
    }
    r = requests.post(url, json=data, headers={"Content-Type": "application/json"})
    result = r.json()
    return result

# ========== 发布文章 ==========
def publish(token, media_id):
    url = f"https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token={token}"
    data = {"media_id": media_id}
    r = requests.post(url, json=data)
    return r.json()

# ========== 主程序 ==========
if __name__ == "__main__":
    print("=" * 50)
    print("CellAgent 微信公众号文章发布")
    print("=" * 50)

    # 获取token
    token = get_token()
    if not token:
        print("❌ 获取token失败")
        sys.exit(1)

    print(f"✅ Token获取成功")

    # 生成文章内容
    content = generate_article_content()
    print(f"✅ 文章内容生成完成")

    # 创建草稿（需要先上传封面图片获取media_id）
    print("\n📋 下一步操作：")
    print("1. 先上传封面图片到公众号素材库")
    print("2. 获取 thumb_media_id")
    print("3. 然后运行发布命令")

    print(f"\n文章标题：CellAgent 项目日志 #001")
    print(f"原文链接：{BASE_URL}")
    print(f"文章长度：{len(content)} 字符")

    # 保存文章内容到文件供查看
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'research', 'wechat_article.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"\n✅ 文章内容已保存到：{output_path}")
    print("请在浏览器打开预览效果")
