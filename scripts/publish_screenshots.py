import requests, os, glob

base = '/Users/apple/cell-agent-platform'
config = {}
with open(os.path.join(base, '.env'), 'r') as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            config[key.strip()] = value.strip()

token = requests.get(f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={config['WECHAT_APPID']}&secret={config['WECHAT_APPSECRET']}").json()['access_token']
print("✅ Token获取成功")

screenshots = sorted(glob.glob(os.path.join(base, 'data/screenshots/screenshot_*.png')))
print(f"📸 找到 {len(screenshots)} 张截图")

# 用第一张截图作为封面，上传获取media_id
print(f"\n📤 上传封面（第1张截图）...")
with open(screenshots[0], 'rb') as f:
    r = requests.post(
        f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image",
        files={'media': ('cover.png', f, 'image/png')}
    )
cover_data = r.json()
thumb_media_id = cover_data.get('media_id', '')
print(f"✅ 封面media_id: {thumb_media_id[:20]}...")

# 上传所有截图获取URL
print(f"\n📤 上传全部截图...")
image_urls = []
for i, img_path in enumerate(screenshots):
    with open(img_path, 'rb') as f:
        r = requests.post(
            f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image",
            files={'media': ('img.png', f, 'image/png')}
        )
    data = r.json()
    if 'url' in data:
        image_urls.append(data['url'])
        print(f"  ✅ {i+1}/{len(screenshots)}")

print(f"\n✅ 上传完成：{len(image_urls)} 张")

# 构建内容
content = ""
for url in image_urls:
    content += f'<p style="text-align:center;"><img src="{url}" style="max-width:100%;" /></p>'
content += '<p style="text-align:center;font-size:14px;color:#999;padding:20px 0;">点击「阅读原文」查看完整动态页面</p>'

# 创建草稿
print("\n📝 创建草稿...")
data = {
    "articles": [{
        "title": "CellAgent日志001",
        "author": "CellAgent",
        "content": content,
        "thumb_media_id": thumb_media_id,
        "content_source_url": "https://zarashirly114-design.github.io/cellagent-site/",
    }]
}
r = requests.post(
    f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}",
    json=data,
    headers={"Content-Type": "application/json"}
)
result = r.json()

if "media_id" in result:
    print(f"\n✅ 草稿创建成功！")
    print(f"请去微信公众平台 → 草稿箱 → 查看并发布")
else:
    print(f"\n❌ 失败：{result}")
