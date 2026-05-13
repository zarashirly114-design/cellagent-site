"""
截取HTML页面截图并发布到微信公众号
"""
import os
import sys
import time
import requests

# 安装依赖
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    os.system("pip3 install playwright")
    os.system("python3 -m playwright install chromium")
    from playwright.sync_api import sync_playwright

# 加载配置
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(base, '.env')
config = {}
with open(env_path, 'r') as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            config[key.strip()] = value.strip()

APPID = config['WECHAT_APPID']
APPSECRET = config['WECHAT_APPSECRET']

def get_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}"
    return requests.get(url).json().get("access_token")

def upload_image(token, image_path):
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    with open(image_path, 'rb') as f:
        files = {'media': (os.path.basename(image_path), f, 'image/png')}
        r = requests.post(url, files=files)
    data = r.json()
    return data.get("media_id"), data.get("url")

def take_screenshots(html_path, output_dir):
    """截取HTML页面为多张图片"""
    os.makedirs(output_dir, exist_ok=True)

    screenshots = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 480, "height": 800})

        # 打开HTML
        file_url = f"file://{os.path.abspath(html_path)}"
        page.goto(file_url, wait_until="networkidle")
        time.sleep(2)

        # 截取整页高度
        total_height = page.evaluate("document.body.scrollHeight")
        print(f"  页面总高度：{total_height}px")

        # 分段截图，每段800px
        viewport_height = 800
        num_screens = (total_height // viewport_height) + 1

        for i in range(num_screens):
            scroll_y = i * viewport_height
            page.evaluate(f"window.scrollTo(0, {scroll_y})")
            time.sleep(0.5)

            output_path = os.path.join(output_dir, f"screenshot_{i+1:02d}.png")
            page.screenshot(path=output_path)
            screenshots.append(output_path)
            print(f"  ✅ 截图 {i+1}/{num_screens}：{output_path}")

        browser.close()

    return screenshots

def create_wechat_article(token, title, image_media_ids, image_urls):
    """用微信图片创建文章"""
    # 构建文章内容（每张图片占一行）
    content_parts = []
    for i, url in enumerate(image_urls):
        content_parts.append(f'<p style="text-align:center;"><img src="{url}" style="max-width:100%;" /></p>')

    # 添加原文链接提示
    content_parts.append('<p style="text-align:center;font-size:14px;color:#999;padding:20px 0;">点击「阅读原文」查看完整动态页面</p>')

    content = "".join(content_parts)

    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    data = {
        "articles": [{
            "title": title,
            "author": "CellAgent",
            "content": content,
            "thumb_media_id": image_media_ids[0],
            "content_source_url": "https://zarashirly114-design.github.io/cellagent-site/",
            "need_open_comment": 1,
        }]
    }
    r = requests.post(url, json=data, headers={"Content-Type": "application/json"})
    return r.json()

if __name__ == "__main__":
    print("=" * 50)
    print("CellAgent 截图发布工具")
    print("=" * 50)

    # 1. 获取token
    token = get_token()
    if not token:
        print("❌ 获取token失败")
        sys.exit(1)
    print("✅ Token获取成功")

    # 2. 截图
    html_path = os.path.join(base, "research", "项目日志001.html")
    output_dir = os.path.join(base, "data", "screenshots")
    print(f"\n📸 开始截图...")
    screenshots = take_screenshots(html_path, output_dir)
    print(f"\n✅ 共截取 {len(screenshots)} 张图片")

    # 3. 上传图片到微信
    print(f"\n📤 上传图片到微信...")
    image_media_ids = []
    image_urls = []
    for i, img_path in enumerate(screenshots):
        media_id, url = upload_image(token, img_path)
        if media_id:
            image_media_ids.append(media_id)
            image_urls.append(url)
            print(f"  ✅ 上传 {i+1}/{len(screenshots)}")
        else:
            print(f"  ❌ 上传失败 {i+1}/{len(screenshots)}")

    print(f"\n✅ 上传完成：{len(image_media_ids)} 张")

    # 4. 创建草稿
    if image_media_ids:
        print(f"\n📝 创建草稿...")
        result = create_wechat_article(
            token,
            "CellAgent项目日志#001：我们用一天验证了一个商业想法",
            image_media_ids,
            image_urls
        )
        if "media_id" in result:
            print(f"\n✅ 草稿创建成功！")
            print(f"   请去微信公众平台 → 草稿箱 → 查看并发布")
        else:
            print(f"\n❌ 创建失败：{result}")
    else:
        print("❌ 没有可用的图片")
