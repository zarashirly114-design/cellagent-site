"""
微信公众号自动发布脚本
"""
import requests
import json
import os
import sys

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

if not APPID or not APPSECRET:
    print("❌ 请先在 .env 文件中配置 WECHAT_APPID 和 WECHAT_APPSECRET")
    sys.exit(1)

# ========== 获取access_token ==========
def get_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}"
    r = requests.get(url)
    data = r.json()
    if "access_token" in data:
        print(f"✅ 获取token成功，有效期：{data['expires_in']}秒")
        return data["access_token"]
    else:
        print(f"❌ 获取token失败：{data}")
        sys.exit(1)

# ========== 上传封面图片 ==========
def upload_image(token, image_path):
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    with open(image_path, 'rb') as f:
        files = {'media': (os.path.basename(image_path), f, 'image/png')}
        r = requests.post(url, files=files)
    data = r.json()
    if "media_id" in data:
        print(f"✅ 图片上传成功：{data['media_id']}")
        return data["media_id"]
    else:
        print(f"❌ 图片上传失败：{data}")
        return None

# ========== 创建草稿 ==========
def create_draft(token, title, content, thumb_media_id, source_url=""):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    data = {
        "articles": [{
            "title": title,
            "author": "CellAgent",
            "content": content,
            "thumb_media_id": thumb_media_id,
            "content_source_url": source_url,
            "need_open_comment": 1,
        }]
    }
    r = requests.post(url, json=data, headers={"Content-Type": "application/json"})
    result = r.json()
    if "media_id" in result:
        print(f"✅ 草稿创建成功：{result['media_id']}")
        return result["media_id"]
    else:
        print(f"❌ 草稿创建失败：{result}")
        return None

# ========== 发布文章 ==========
def publish(token, media_id):
    url = f"https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token={token}"
    data = {"media_id": media_id}
    r = requests.post(url, json=data)
    result = r.json()
    if result.get("errcode", 0) == 0:
        print(f"✅ 发布成功！publish_id: {result.get('publish_id', '')}")
        return result
    else:
        print(f"❌ 发布失败：{result}")
        return None

# ========== 主程序 ==========
if __name__ == "__main__":
    print("=" * 50)
    print("CellAgent 微信公众号发布工具")
    print("=" * 50)

    token = get_token()

    print(f"\nAppID: {APPID[:6]}****")
    print(f"Token: {token[:20]}...")
    print("\n✅ 配置正确，可以开始发布文章了！")
    print("\n可用命令：")
    print("  python3 scripts/wechat_publisher.py          - 测试连接")
    print("  python3 scripts/wechat_publisher.py publish  - 发布文章")
