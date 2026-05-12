import sqlite3
import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'landing.db')

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_type TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            company TEXT DEFAULT '',
            city TEXT DEFAULT '',
            interest TEXT DEFAULT '',
            message TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS page_views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page TEXT DEFAULT 'landing',
            ip TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    conn.close()

LANDING_HTML = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CellAgent</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,sans-serif;background:#0a0f1a;color:#f1f5f9;line-height:1.6}
.container{max-width:640px;margin:0 auto;padding:0 20px;position:relative;z-index:1}
.header{text-align:center;padding:48px 0 32px}
.logo{font-size:28px;font-weight:900;color:#c9a84c}
.logo-sub{font-size:13px;color:#94a3b8;letter-spacing:2px}
.hero{text-align:center;padding:24px 0 40px}
.hero h1{font-size:26px;font-weight:800;margin-bottom:12px;background:linear-gradient(135deg,#f1f5f9,#c9a84c);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero p{font-size:15px;color:#94a3b8}
.stats{display:flex;gap:16px;margin-bottom:24px}
.stat-card{flex:1;background:#111827;border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:20px;text-align:center}
.stat-num{font-size:32px;font-weight:900;color:#c9a84c}
.stat-label{font-size:12px;color:#94a3b8;margin-top:4px}
.products{background:#111827;border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:28px;margin-bottom:24px}
.products h2{font-size:18px;margin-bottom:20px;color:#c9a84c}
.product-item{display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.06)}
.product-item:last-child{border-bottom:none}
.product-tag{display:inline-block;padding:3px 10px;border-radius:4px;font-size:11px;font-weight:600;flex-shrink:0}
.tag-cart{background:rgba(239,68,68,0.15);color:#f87171}
.tag-stem{background:rgba(34,197,94,0.15);color:#4ade80}
.tag-til{background:rgba(59,130,246,0.15);color:#60a5fa}
.product-name{font-size:14px;flex:1}
.product-company{font-size:12px;color:#64748b}
.form-card{background:#111827;border:1px solid rgba(201,168,76,0.2);border-radius:16px;padding:28px;margin-bottom:24px}
.form-card h2{font-size:18px;margin-bottom:4px}
.subtitle{font-size:13px;color:#94a3b8;margin-bottom:20px}
.form-group{margin-bottom:14px}
.form-group label{display:block;font-size:13px;color:#94a3b8;margin-bottom:6px}
.form-input{width:100%;padding:12px 16px;border-radius:10px;background:#0a0f1a;border:1px solid rgba(255,255,255,0.1);color:#f1f5f9;font-size:15px;font-family:inherit}
.form-input:focus{outline:none;border-color:#c9a84c}
.form-input::placeholder{color:#4a5568}
.type-selector{display:flex;gap:10px;margin-bottom:16px}
.type-option{flex:1;padding:14px 12px;border-radius:10px;border:2px solid rgba(255,255,255,0.1);background:transparent;color:#94a3b8;cursor:pointer;text-align:center;font-family:inherit;font-size:14px}
.type-option:hover{border-color:rgba(201,168,76,0.3)}
.type-option.selected{border-color:#c9a84c;background:rgba(201,168,76,0.1);color:#c9a84c}
.type-icon{font-size:24px;display:block;margin-bottom:6px}
.form-row{display:flex;gap:12px}
.form-row .form-group{flex:1}
.btn-submit{width:100%;padding:14px;border-radius:10px;background:#c9a84c;color:#0a0f1a;font-size:16px;font-weight:700;border:none;cursor:pointer;font-family:inherit;margin-top:8px}
.btn-submit:hover{background:#dbb960}
.btn-submit:disabled{background:#4a5568;cursor:not-allowed}
.success-msg{display:none;text-align:center;padding:32px}
.success-msg.show{display:block}
.success-icon{font-size:48px;margin-bottom:16px}
.success-msg h2{font-size:20px;margin-bottom:8px;color:#4ade80}
.success-msg p{font-size:14px;color:#94a3b8}
.footer{text-align:center;padding:24px 0 40px;font-size:12px;color:#4a5568}
@media(max-width:480px){.type-selector{flex-direction:column}.form-row{flex-direction:column;gap:0}.stats{flex-direction:column}}
</style>
</head>
<body>
<div class="container">
<div class="header">
<div class="logo">CellAgent</div>
<div class="logo-sub">细胞代理通</div>
</div>
<div class="hero">
<h1>细胞治疗产品代理机会</h1>
<p>15款细胞治疗产品及细胞存储服务正在寻找区域代理商</p>
</div>
<div class="stats">
<div class="stat-card"><div class="stat-num">15</div><div class="stat-label">可代理产品/服务</div></div>
<div class="stat-card"><div class="stat-num">67</div><div class="stat-label">入库企业</div></div>
<div class="stat-card"><div class="stat-num">42</div><div class="stat-label">在研管线</div></div>
</div>
<div class="products">
<h2>可代理产品与服务清单</h2>
<div class="product-item"><span class="product-tag tag-cart">CAR-T</span><span class="product-name">奕凯达</span><span class="product-company">复星凯特</span></div>
<div class="product-item"><span class="product-tag tag-cart">CAR-T</span><span class="product-name">倍诺达</span><span class="product-company">药明巨诺</span></div>
<div class="product-item"><span class="product-tag tag-cart">CAR-T</span><span class="product-name">福可苏</span><span class="product-company">科济药业</span></div>
<div class="product-item"><span class="product-tag tag-cart">CAR-T</span><span class="product-name">源瑞达</span><span class="product-company">合源生物</span></div>
<div class="product-item"><span class="product-tag tag-cart">CAR-T</span><span class="product-name">赛恺泽</span><span class="product-company">科济药业</span></div>
<div class="product-item"><span class="product-tag tag-cart">CAR-T</span><span class="product-name">卡卫荻</span><span class="product-company">传奇生物</span></div>
<div class="product-item"><span class="product-tag tag-stem">干细胞</span><span class="product-name">睿铂生</span><span class="product-company">铂生卓越</span></div>
<div class="product-item"><span class="product-tag tag-til">TIL</span><span class="product-name">GC203</span><span class="product-company">君赛生物</span></div>
<div class="product-item"><span class="product-tag tag-stem">存储</span><span class="product-name">细胞存储服务</span><span class="product-company">上海细胞治疗集团</span></div>
<div class="product-item"><span class="product-tag tag-stem">存储</span><span class="product-name">细胞存储服务</span><span class="product-company">北科生物</span></div>
<div class="product-item"><span class="product-tag tag-stem">存储</span><span class="product-name">细胞存储服务</span><span class="product-company">中源协和</span></div>
<div class="product-item"><span class="product-tag tag-stem">存储</span><span class="product-name">细胞存储服务</span><span class="product-company">博雅干细胞</span></div>
<div class="product-item"><span class="product-tag tag-stem">存储</span><span class="product-name">细胞存储服务</span><span class="product-company">深圳泽医</span></div>
<div class="product-item"><span class="product-tag tag-stem">存储</span><span class="product-name">细胞存储服务</span><span class="product-company">汉氏联合</span></div>
<div class="product-item"><span class="product-tag tag-stem">存储</span><span class="product-name">细胞存储服务</span><span class="product-company">南华生物</span></div>
</div>
<div class="form-card" id="form-section">
<h2>登记代理意向</h2>
<p class="subtitle">填写信息后平台上线第一时间通知您</p>
<form id="register-form" onsubmit="submitForm(event)">
<div class="type-selector">
<button type="button" class="type-option selected" onclick="selectType(this,'agent')"><span class="type-icon">🤝</span>我想找产品代理</button>
<button type="button" class="type-option" onclick="selectType(this,'company')"><span class="type-icon">🏢</span>我有产品要招商</button>
</div>
<div class="form-row">
<div class="form-group"><label>姓名 *</label><input type="text" class="form-input" id="name" placeholder="您的姓名" required></div>
<div class="form-group"><label>手机号 *</label><input type="tel" class="form-input" id="phone" placeholder="手机号" required></div>
</div>
<div class="form-row">
<div class="form-group"><label>所在城市</label><input type="text" class="form-input" id="city" placeholder="如：上海"></div>
<div class="form-group"><label>公司名称</label><input type="text" class="form-input" id="company" placeholder="选填"></div>
</div>
<div class="form-group"><label>感兴趣的产品</label><input type="text" class="form-input" id="interest" placeholder="如：CAR-T、干细胞"></div>
<div class="form-group"><label>补充说明</label><input type="text" class="form-input" id="message" placeholder="渠道资源或需求（选填）"></div>
<button type="submit" class="btn-submit" id="btn-submit">提交代理意向</button>
</form>
<div class="success-msg" id="success-msg">
<div class="success-icon">✅</div>
<h2>提交成功！</h2>
<p>平台上线后第一时间通知您</p>
</div>
</div>
<div class="footer">CellAgent — 细胞治疗行业代理商招募平台</div>
</div>
<script>
var selectedType='agent';
function selectType(el,type){document.querySelectorAll('.type-option').forEach(function(o){o.classList.remove('selected')});el.classList.add('selected');selectedType.type;document.getElementById('btn-submit').textContent=type==='agent'?'提交代理意向':'提交招商信息'}
function submitForm(e){e.preventDefault();var btn=document.getElementById('btn-submit');btn.disabled=true;btn.textContent='提交中...';var data={user_type:selectedType,name:document.getElementById('name').value,phone:document.getElementById('phone').value,city:document.getElementById('city').value,company:document.getElementById('company').value,interest:document.getElementById('interest').value,message:document.getElementById('message').value};fetch('/api/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}).then(function(r){return r.json()}).then(function(result){if(result.success){document.getElementById('register-form').style.display='none';document.getElementById('success-msg').classList.add('show')}else{alert(result.error||'提交失败');btn.disabled=false}}).catch(function(){alert('网络错误');btn.disabled=false})}
</script>
</body>
</html>'''

ADMIN_HTML = '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>CellAgent验证数据</title>
<style>
body{font-family:-apple-system,sans-serif;background:#0a0f1a;color:#f1f5f9;padding:40px}
h1{color:#c9a84c;margin-bottom:32px}
.stats{display:flex;gap:20px;margin-bottom:32px}
.stat{background:#111827;border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:24px;flex:1;text-align:center}
.stat-num{font-size:42px;font-weight:900;color:#c9a84c}
.stat-label{font-size:14px;color:#94a3b8;margin-top:4px}
table{width:100%;border-collapse:collapse;background:#111827;border-radius:12px;overflow:hidden}
th{text-align:left;padding:14px 16px;background:rgba(255,255,255,0.03);color:#94a3b8;font-size:13px}
td{padding:14px 16px;border-bottom:1px solid rgba(255,255,255,0.06);font-size:14px}
.tag{display:inline-block;padding:3px 10px;border-radius:4px;font-size:12px}
.tag-agent{background:rgba(34,197,94,0.15);color:#4ade80}
.tag-company{background:rgba(59,130,246,0.15);color:#60a5fa}
</style></head><body>
<h1>CellAgent 验证数据面板</h1>
<div class="stats">
<div class="stat"><div class="stat-num">VIEWS</div><div class="stat-label">页面浏览</div></div>
<div class="stat"><div class="stat-num">TOTAL</div><div class="stat-label">总注册</div></div>
<div class="stat"><div class="stat-num">AGENTS</div><div class="stat-label">代理商意向</div></div>
<div class="stat"><div class="stat-num">COMPANIES</div><div class="stat-label">企业意向</div></div>
<div class="stat"><div class="stat-num">RATE</div><div class="stat-label">转化率</div></div>
</div>
<table><thead><tr><th>类型</th><th>姓名</th><th>手机号</th><th>城市</th><th>公司</th><th>感兴趣产品</th><th>备注</th><th>时间</th></tr></thead><tbody>ROWS</tbody></table>
<script>setTimeout(function(){location.reload()},10000)</script>
</body></html>'''

@app.route('/')
def landing():
    conn = get_db()
    ip = request.remote_addr
    conn.execute('INSERT INTO page_views (ip) VALUES (?)', (ip,))
    conn.commit()
    conn.close()
    return render_template_string(LANDING_HTML)

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    user_type = data.get('user_type', 'agent')
    if not name or not phone:
        return jsonify({'success': False, 'error': '姓名和手机号不能为空'})
    conn = get_db()
    existing = conn.execute('SELECT id FROM registrations WHERE phone = ?', (phone,)).fetchone()
    if existing:
        conn.close()
        return jsonify({'success': False, 'error': '该手机号已登记'})
    conn.execute('INSERT INTO registrations (user_type,name,phone,company,city,interest,message) VALUES (?,?,?,?,?,?,?)',
        (user_type, name, phone, data.get('company',''), data.get('city',''), data.get('interest',''), data.get('message','')))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/admin/results')
def admin_results():
    conn = get_db()
    regs = conn.execute('SELECT * FROM registrations ORDER BY created_at DESC').fetchall()
    views = conn.execute('SELECT COUNT(*) as cnt FROM page_views').fetchone()['cnt']
    total = len(regs)
    agents = sum(1 for r in regs if r['user_type'] == 'agent')
    companies = sum(1 for r in regs if r['user_type'] == 'company')
    rate = round(total / views * 100, 1) if views > 0 else 0

    rows = ''
    for r in regs:
        tc = 'tag-agent' if r['user_type'] == 'agent' else 'tag-company'
        tt = '代理商' if r['user_type'] == 'agent' else '企业'
        rows += '<tr><td><span class="tag ' + tc + '">' + tt + '</span></td><td>' + str(r['name']) + '</td><td>' + str(r['phone']) + '</td><td>' + str(r['city']) + '</td><td>' + str(r['company']) + '</td><td>' + str(r['interest']) + '</td><td>' + str(r['message']) + '</td><td>' + str(r['created_at']) + '</td></tr>'

    html = ADMIN_HTML.replace('VIEWS', str(views)).replace('TOTAL', str(total)).replace('AGENTS', str(agents)).replace('COMPANIES', str(companies)).replace('RATE', str(rate) + '%').replace('ROWS', rows)
    conn.close()
    return html

if __name__ == '__main__':
    init_db()
    print('=' * 60)
    print('CellAgent 验证落地页已启动')
    print('=' * 60)
    print('注册页面: http://localhost:5001')
    print('数据后台: http://localhost:5001/admin/results')
    print('=' * 60)
    app.run(host='0.0.0.0', port=5001, debug=True)
