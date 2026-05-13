import re, requests, os

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
config = {}
with open(env_path, 'r') as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            config[key.strip()] = value.strip()

APPID = config['WECHAT_APPID']
APPSECRET = config['WECHAT_APPSECRET']

url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}"
token = requests.get(url).json()['access_token']
print(f"✅ Token获取成功")

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(base, 'data', 'cover_media_id.txt')) as f:
    thumb_media_id = f.read().strip()

with open(os.path.join(base, 'research', '项目日志001.html'), 'r', encoding='utf-8') as f:
    html = f.read()

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
    'var(--text)': '#f1f5f9',
    'var(--text-muted)': '#94a3b8',
    'var(--text-dim)': '#64748b',
    'var(--border)': 'rgba(255,255,255,0.08)',
}
for old, new in replacements.items():
    html = html.replace(old, new)

print(f"✅ 内容准备完成")

title = "CellAgent项目日志#001"

api_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
data = {
    "articles": [{
        "title": title,
        "author": "CellAgent",
        "content": html.strip(),
        "thumb_media_id": thumb_media_id,
        "content_source_url": "https://zarashirly114-design.github.io/cellagent-site/",
    }]
}
r = requests.post(api_url, json=data, headers={"Content-Type": "application/json"})
result = r.json()

if "media_id" in result:
    print(f"✅ 草稿创建成功！")
    print(f"media_id: {result['media_id']}")
    print(f"请去微信公众平台 - 草稿箱 查看并发布")
else:
    print(f"❌ 失败：{result}")
