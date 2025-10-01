import requests
from bs4 import BeautifulSoup

def debug_template():
    base_url = "http://localhost:10000"
    session = requests.Session()
    
    # 登录
    login_page = session.get(f"{base_url}/auth/login")
    soup = BeautifulSoup(login_page.text, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrf_token'})
    
    login_data = {
        'username': 'NIJIE',
        'password': '123456'
    }
    
    if csrf_token:
        login_data['csrf_token'] = csrf_token['value']
    
    login_response = session.post(f"{base_url}/auth/login", data=login_data)
    
    if login_response.status_code == 200 and 'login' not in login_response.url:
        print("登录成功")
        
        # 测试招标中阶段过滤
        filter_url = f"{base_url}/project/?filter_current_stage=tendering"
        response = session.get(filter_url)
        
        if response.status_code == 200:
            # 保存完整的HTML到文件进行分析
            with open('debug_response.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("HTML响应已保存到 debug_response.html")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 检查按钮
            stage_btn = soup.find('button', {'id': 'stageSelectorBtn'})
            if stage_btn:
                print(f"找到按钮: {stage_btn}")
                print(f"按钮内容: '{stage_btn.get_text().strip()}'")
                
                # 检查按钮的HTML结构
                print("按钮HTML:")
                print(stage_btn.prettify())
            else:
                print("未找到阶段选择按钮")
            
            # 检查菜单
            menu = soup.find('ul', {'id': 'stageSelectorMenu'})
            if menu:
                print("\n找到菜单:")
                items = menu.find_all('a', {'data-stage': True})
                for item in items:
                    stage = item.get('data-stage')
                    classes = item.get('class', [])
                    text = item.get_text().strip()
                    print(f"  {stage}: {text} - 类: {classes}")
            else:
                print("未找到阶段选择菜单")
                
            # 检查URL参数是否正确传递
            print(f"\n请求URL: {filter_url}")
            print(f"响应URL: {response.url}")
            
            # 检查是否有JavaScript错误或其他问题
            if 'current_stage_filter' in response.text:
                print("✓ 响应包含 current_stage_filter")
            else:
                print("✗ 响应不包含 current_stage_filter")
                
            # 搜索特定的模板代码
            if 'tendering' in response.text and '招标中' in response.text:
                print("✓ 响应包含 tendering 和 招标中")
            else:
                print("✗ 响应不包含 tendering 或 招标中")
        else:
            print(f"请求失败: {response.status_code}")
    else:
        print("登录失败")

if __name__ == "__main__":
    debug_template() 