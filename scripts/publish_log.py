"""
直接读取已有HTML发布到微信公众号
"""
import requests
import os
import sys
import re

# 加载配置
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
config = {}
with open(env_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            config[key.strip()] = value.strip()

APPID = config.get('WECHAT_APPID', '')
APPSECRET = config.get('WECHAT_APPSECRET', '')

def get_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}"
    r = requests.get(url)
    return r.json().get("access_token")

def get_thumb_media_id():
    mid_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'cover_media_id.txt')
    with open(mid_path, 'r') as f:
        return f.read().strip()

def convert_for_wechat(html):
    html = re.sub(r'<link[^>]*>', '', html)
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    html = re.sub(r'<!DOCTYPE[^>]*>', '', html)
    html = re.sub(r'<html[^>]*>', '', html)
    html = re.sub(r'</html>', '', html)
    html = re.sub(r'<head[^>]*>.*?</head>', '', html, flags=re.DOTALL)
    html = re.sub(r'<body[^>]*>', '', html)
    html = re.sub(r'</body>', '', html)
    replacements = {
        'var(--bg)': '#0a0f1a',
        'var(--surface)': '#111827',
        'var(--accent)': '#c9a84c',
        'var(--green)': '#22c55e',
        'var(--blue)': '#3b82f6',
        'var(--purple)': '#a855f7',
        'var(--text)': '#f1f5f9',
        'var(--text-muted)': '#94a3b8',
        'var(--text-dim)': '#64748b',
        'var(--border)': 'rgba(255,255,255,0.08)',
    }
    for old, new in replacements.items():
        html = html.replace(old, new)
    return html.strip()

def create_draft(token, title, content, thumb_media_id):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    data = {
        "articles": [{
            "title": title,
            "author": "CellAgent",
            "content": content,
            "thumb_media_id": thumb_media_id,
            "content_source_url": "https://zarashirly114-design.github.io/cellagent-site/",
        }]
    }
    r = requests.post(url, json=data, headers={"Content-Type": "application/json"})
    return r.json()

if __name__ == "__main__":
    print("=" * 50)
    print("CellAgent 发布项目日志")
    print("=" * 50)

    token = get_token()
    if not token:
        print("❌ 获取token失败")
        sys.exit(1)
    print("✅ Token获取成功")

    # 读取封面media_id
    thumb_media_id = get_thumb_media_id()
    print(f"✅ 封面media_id: {thumb_media_id[:20]}...")

    # 读取HTML
    html_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'research', '项目日志001.html')
    print(f"📂 读取文件：{html_path}")
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    print(f"✅ 文件读取成功（{len(html_content)} 字符）")

    # 转换格式
    wechat_content = convert_for_wechat(html_content)
    print(f"✅ 格式转换完成（{len(wechat_content)} 字符）")

    # 保存预览
    preview_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'research', 'wechat_preview.html')
    with open(preview_path, 'w', encoding='utf-8') as f:
        f.write(f'<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head><body style="margin:0;padding:0;background:#0a0f1a;">{wechat_content}</body></html>')
    print(f"✅ 预览已保存：{preview_path}")

    # 创建草稿
    print("\n📝 正在创建草稿...")
    result = create_draft(token, "CellAgent 项目日志 #001｜我们用一天验证了一个商业想法", wechat_content, thumb_media_id)

    if "media_id" in result:
        print(f"✅ 草稿创建成功！")
        print(f"   media_id: {result['media_id']}")
        print(f"\n📋 下一步：")
        print(f"   1. 打开微信公众平台 → 草稿箱")
        print(f"   2. 查看文章，确认无误后发布")
    else:
        print(f"❌ 创建失败：{result}")
