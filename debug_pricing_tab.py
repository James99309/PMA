#!/usr/bin/env python3
"""
调试批价单审批页签
"""

import requests
from bs4 import BeautifulSoup

def debug_pricing_tab():
    """调试批价单审批页签"""
    base_url = "http://localhost:10000"
    
    # 测试登录
    session = requests.Session()
    
    # 获取登录页面
    login_page = session.get(f"{base_url}/auth/login")
    print(f"获取登录页面状态: {login_page.status_code}")
    
    soup = BeautifulSoup(login_page.content, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrf_token'})
    
    if not csrf_token:
        print("❌ 无法找到CSRF token")
        return
    
    print(f"CSRF token: {csrf_token['value'][:20]}...")
    
    # 登录
    login_data = {
        'username': 'NIJIE',
        'password': '123456',
        'csrf_token': csrf_token['value']
    }
    
    login_response = session.post(f"{base_url}/auth/login", data=login_data, allow_redirects=False)
    print(f"登录响应状态: {login_response.status_code}")
    print(f"登录响应头: {dict(login_response.headers)}")
    
    # 检查是否重定向到首页
    if login_response.status_code == 302:
        print("✅ 登录成功，发生重定向")
        redirect_url = login_response.headers.get('Location', '')
        print(f"重定向到: {redirect_url}")
    else:
        print("❌ 登录可能失败，没有重定向")
        # 检查响应内容
        if "用户名或密码错误" in login_response.text:
            print("❌ 用户名或密码错误")
            return
    
    # 访问首页确认登录状态
    home_page = session.get(f"{base_url}/")
    print(f"首页访问状态: {home_page.status_code}")
    
    if "欢迎登录" in home_page.text:
        print("❌ 仍然显示登录页面，登录失败")
        return
    else:
        print("✅ 登录状态确认成功")
    
    # 访问审批中心默认页面
    approval_center = session.get(f"{base_url}/approval/center")
    print(f"审批中心状态: {approval_center.status_code}")
    
    # 访问批价单审批页签
    pricing_tab = session.get(f"{base_url}/approval/center?tab=pricing_order")
    print(f"批价单页签状态: {pricing_tab.status_code}")
    
    # 检查是否还是登录页面
    if "欢迎登录" in pricing_tab.text:
        print("❌ 批价单页签返回登录页面")
        return
    
    # 保存HTML内容到文件
    with open('pricing_tab_debug.html', 'w', encoding='utf-8') as f:
        f.write(pricing_tab.text)
    
    print("✅ HTML内容已保存到 pricing_tab_debug.html")
    
    # 解析HTML
    soup = BeautifulSoup(pricing_tab.content, 'html.parser')
    
    # 查找页面标题
    title = soup.find('title')
    if title:
        print(f"页面标题: {title.get_text()}")
    
    # 查找审批中心标题
    h1_tags = soup.find_all('h1')
    for h1 in h1_tags:
        if "审批中心" in h1.get_text():
            print(f"找到审批中心标题: {h1.get_text().strip()}")
    
    # 查找表格
    tables = soup.find_all('table')
    print(f"找到 {len(tables)} 个表格")
    
    for i, table in enumerate(tables):
        print(f"\n表格 {i+1}:")
        headers = table.find_all('th')
        if headers:
            header_texts = [th.get_text().strip() for th in headers]
            print(f"  表头: {header_texts}")
        
        rows = table.find_all('tr')
        data_rows = [row for row in rows if row.find('td')]
        print(f"  数据行数: {len(data_rows)}")
        
        if data_rows:
            for j, row in enumerate(data_rows[:3]):  # 只显示前3行
                cells = row.find_all('td')
                cell_texts = [cell.get_text().strip() for cell in cells]
                print(f"    行 {j+1}: {cell_texts}")
    
    # 查找徽章
    badges = soup.find_all('span', class_='badge')
    print(f"\n找到 {len(badges)} 个徽章:")
    for badge in badges[:10]:  # 只显示前10个
        print(f"  - {badge.get_text().strip()}")
    
    # 查找空数据提示
    empty_messages = soup.find_all(text=lambda text: text and ("暂无" in text or "没有" in text))
    if empty_messages:
        print(f"\n找到空数据提示:")
        for msg in empty_messages[:5]:
            print(f"  - {msg.strip()}")

if __name__ == "__main__":
    debug_pricing_tab() 