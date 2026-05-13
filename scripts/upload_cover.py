"""
生成封面图片并上传到微信公众号素材库
"""
import requests
import os
import sys

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

def create_cover_image():
    """用Python生成封面图片"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        os.system("pip3 install Pillow")
        from PIL import Image, ImageDraw, ImageFont

    # 创建900x383封面（微信推荐比例）
    img = Image.new('RGB', (900, 383), color=(10, 15, 26))
    draw = ImageDraw.Draw(img)

    # 画装饰线
    draw.rectangle([0, 360, 900, 383], fill=(201, 168, 76))

    # 写文字
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 64)
        font_small = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 24)
        font_tiny = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 18)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_tiny = ImageFont.load_default()

    # 标题
    draw.text((80, 100), "CellAgent", fill=(201, 168, 76), font=font_large)
    draw.text((80, 180), "项目日志 #001", fill=(148, 163, 184), font=font_small)
    draw.text((80, 230), "我们用一天验证了一个商业想法", fill=(241, 245, 249), font=font_small)
    draw.text((80, 320), "2026.05.12", fill=(100, 116, 139), font=font_tiny)

    # 保存
    cover_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'cover.png')
    img.save(cover_path, 'PNG')
    print(f"✅ 封面图片已生成：{cover_path}")
    return cover_path

def upload_image(token, image_path):
    """上传图片到微信素材库"""
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    with open(image_path, 'rb') as f:
        files = {'media': ('cover.png', f, 'image/png')}
        r = requests.post(url, files=files)
    data = r.json()
    if "media_id" in data:
        print(f"✅ 上传成功！media_id: {data['media_id']}")
        return data["media_id"]
    else:
        print(f"❌ 上传失败：{data}")
        return None

if __name__ == "__main__":
    print("=" * 50)
    print("上传封面图片")
    print("=" * 50)

    token = get_token()
    if not token:
        print("❌ 获取token失败")
        sys.exit(1)

    # 生成封面
    cover_path = create_cover_image()

    # 上传
    media_id = upload_image(token, cover_path)

    if media_id:
        # 保存media_id到文件
        mid_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'cover_media_id.txt')
        with open(mid_path, 'w') as f:
            f.write(media_id)
        print(f"\n✅ media_id已保存到：{mid_path}")
        print(f"\n现在可以运行：python3 scripts/publish_log.py")
