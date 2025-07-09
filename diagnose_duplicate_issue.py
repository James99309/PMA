#!/usr/bin/env python3
"""
诊断重复检测问题的完整脚本
"""

import re
import difflib

def normalize_company_name(name):
    """标准化公司名称，用于重复检测 - 更精确的匹配逻辑"""
    if not name:
        return ""
    
    original_name = name
    
    # 1. 清理不可见字符和额外空格
    normalized = re.sub(r'\s+', '', name.strip())  # 去除所有空白字符
    normalized = re.sub(r'[^\w\u4e00-\u9fff]', '', normalized)  # 只保留字母、数字和中文
    
    # 2. 去除地名前缀（更精确的地名识别）
    location_prefixes = [
        # 直辖市
        "北京市", "上海市", "天津市", "重庆市",
        "北京", "上海", "天津", "重庆",
        # 常见省份简称
        "广东省", "浙江省", "江苏省", "山东省", "河南省", "四川省", "湖北省", "湖南省",
        "广东", "浙江", "江苏", "山东", "河南", "四川", "湖北", "湖南",
        "福建", "安徽", "江西", "云南", "贵州", "山西", "陕西", "甘肃",
        "青海", "海南", "台湾", "香港", "澳门",
        # 常见城市
        "深圳市", "广州市", "杭州市", "南京市", "苏州市", "无锡市", "常州市",
        "深圳", "广州", "杭州", "南京", "苏州", "无锡", "常州",
        "宁波", "温州", "东莞", "佛山", "中山", "珠海", "厦门",
        "青岛", "大连", "沈阳", "长春", "哈尔滨", "西安", "成都",
        "武汉", "长沙", "郑州", "济南", "石家庄", "太原", "呼和浩特",
        # 开发区等
        "经济技术开发区", "高新技术开发区", "工业园区", "科技园区",
        "开发区", "高新区", "工业区", "科技园"
    ]
    
    # 按长度排序，先匹配长的地名
    location_prefixes.sort(key=len, reverse=True)
    
    removed_prefix = None
    for prefix in location_prefixes:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]
            removed_prefix = prefix
            break
    
    # 3. 去除公司类型后缀
    business_suffixes = [
        # 标准公司类型
        "有限责任公司", "股份有限公司", "有限公司", "股份公司",
        # 特殊组织形式
        "集团有限公司", "控股有限公司", "投资有限公司",
        "集团股份有限公司", "控股股份有限公司",
        # 简化形式
        "有限", "股份", "集团", "控股", "投资",
        # 英文后缀
        "Co.,Ltd", "Co.Ltd", "Ltd", "Inc", "Corp", "LLC",
        "Company", "Corporation", "Limited", "Incorporated"
    ]
    
    # 按长度排序，先匹配长的后缀
    business_suffixes.sort(key=len, reverse=True)
    
    removed_suffix = None
    for suffix in business_suffixes:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)]
            removed_suffix = suffix
            break
    
    # 4. 再次清理可能的空格
    normalized = re.sub(r'\s+', '', normalized)
    
    result = normalized.lower()
    
    print(f"标准化过程: '{original_name}'")
    print(f"  1. 清理空格和特殊字符: '{normalized}'")
    if removed_prefix:
        print(f"  2. 移除地名前缀: '{removed_prefix}'")
    if removed_suffix:
        print(f"  3. 移除公司后缀: '{removed_suffix}'")
    print(f"  4. 最终结果: '{result}'")
    print()
    
    return result

def find_similar_companies_detailed(target_company, all_companies):
    """查找相似的公司，返回详细的匹配过程"""
    similar_companies = []
    target_normalized = normalize_company_name(target_company['company_name'])
    
    print(f"=== 查找与 '{target_company['company_name']}' 相似的公司 ===")
    print(f"目标公司标准化后: '{target_normalized}'")
    print()
    
    for company in all_companies:
        if company['id'] == target_company['id']:
            continue
            
        company_normalized = normalize_company_name(company['company_name'])
        
        print(f"对比公司: '{company['company_name']}'")
        print(f"对比公司标准化后: '{company_normalized}'")
        
        # 1. 首先检查完全匹配
        if target_normalized == company_normalized:
            final_score = 1.0
            print(f"  ✓ 完全匹配! 得分: {final_score:.3f}")
        else:
            # 2. 检查核心企业名称的长度，太短的不作为匹配候选
            if len(target_normalized) < 3 or len(company_normalized) < 3:
                final_score = 0
                print(f"  ✗ 名称太短，跳过匹配 (长度: {len(target_normalized)} vs {len(company_normalized)})")
            else:
                # 3. 计算基础相似度
                similarity = difflib.SequenceMatcher(None, target_normalized, company_normalized).ratio()
                
                # 4. 更严格的包含关系检查
                containment_bonus = 0
                if len(target_normalized) >= 4 and len(company_normalized) >= 4:
                    # 只有当名称足够长时才考虑包含关系
                    if target_normalized in company_normalized or company_normalized in target_normalized:
                        # 计算包含关系的权重，避免过度匹配
                        shorter_len = min(len(target_normalized), len(company_normalized))
                        longer_len = max(len(target_normalized), len(company_normalized))
                        length_ratio = shorter_len / longer_len
                        
                        # 只有当长度比例合理时才给予包含关系加权
                        if length_ratio > 0.7:  # 长度差异不能太大
                            containment_bonus = 0.15 * length_ratio
                            print(f"  包含关系加权: {containment_bonus:.3f} (长度比例: {length_ratio:.3f})")
                
                final_score = min(1.0, similarity + containment_bonus)
                print(f"  基础相似度: {similarity:.3f}")
                print(f"  包含关系加权: {containment_bonus:.3f}")
                print(f"  最终得分: {final_score:.3f}")
        
        # 检查是否超过阈值
        threshold = 0.85
        will_match = final_score > threshold
        print(f"  阈值: {threshold}, 是否匹配: {'✓' if will_match else '✗'}")
        print()
        
        if will_match:
            similar_companies.append({
                'company': company,
                'similarity': final_score,
                'match_type': 'high' if final_score > 0.8 else 'medium' if final_score > 0.6 else 'low'
            })
    
    return similar_companies

def diagnose_duplicate_detection():
    """诊断重复检测问题"""
    print("=== 诊断重复检测问题 ===\n")
    
    # 模拟数据库中的实际记录
    companies = [
        {
            'id': 300,
            'company_name': '上海瑞康通信科技有限公司 ',  # 末尾有空格
            'company_code': '25E09297',
            'owner_id': 15,
            'owner_name': '李华伟',
            'created_at': '2024-02-21 15:18:26',
        },
        {
            'id': 424,
            'company_name': '       上海瑞康通信科技有限公司',  # 开头有空格
            'company_code': '25E09421',
            'owner_id': 2,
            'owner_name': '方玲',
            'created_at': '2025-04-17 00:00:00',
        }
    ]
    
    print("数据库中的瑞康公司记录:")
    for company in companies:
        char_codes = [ord(c) for c in company['company_name']]
        print(f"ID {company['id']}: '{company['company_name']}'")
        print(f"  长度: {len(company['company_name'])} 字符")
        print(f"  字符编码: {char_codes}")
        print(f"  所有者: {company['owner_name']}")
        print()
    
    # 测试标准化
    print("=== 标准化测试 ===")
    for company in companies:
        normalize_company_name(company['company_name'])
    
    # 测试相似度计算
    print("=== 相似度计算测试 ===")
    target_company = companies[0]  # ID 300
    similar = find_similar_companies_detailed(target_company, companies)
    
    print(f"找到 {len(similar)} 个相似公司:")
    for item in similar:
        company = item['company']
        print(f"  - ID {company['id']}: '{company['company_name']}' (相似度: {item['similarity']:.3f})")
    
    # 模拟detect_duplicates的完整逻辑
    print("\n=== 模拟完整的detect_duplicates逻辑 ===")
    
    duplicate_suggestions = []
    processed_companies = set()
    
    for company in companies:
        if company['id'] in processed_companies:
            continue
            
        similar_companies_data = find_similar_companies_detailed(company, companies)
        
        if similar_companies_data:
            processed_companies.add(company['id'])
            
            # 将所有相关公司标记为已处理
            for item in similar_companies_data:
                processed_companies.add(item['company']['id'])
            
            max_similarity = max(item['similarity'] for item in similar_companies_data)
            
            suggestion = {
                'target_company': company,
                'similar_companies': [item['company'] for item in similar_companies_data],
                'max_similarity': max_similarity,
                'total_companies': 1 + len(similar_companies_data)
            }
            duplicate_suggestions.append(suggestion)
    
    print(f"最终检测结果: 找到 {len(duplicate_suggestions)} 个重复组")
    
    for i, suggestion in enumerate(duplicate_suggestions):
        print(f"重复组 {i+1}:")
        print(f"  目标公司: ID {suggestion['target_company']['id']} - {suggestion['target_company']['company_name']}")
        print(f"  相似公司数: {len(suggestion['similar_companies'])}")
        print(f"  最高匹配度: {suggestion['max_similarity']:.3f}")
        for similar in suggestion['similar_companies']:
            print(f"    - ID {similar['id']}: {similar['company_name']}")
        print()
    
    return len(duplicate_suggestions) > 0

if __name__ == "__main__":
    success = diagnose_duplicate_detection()
    
    print("=== 诊断结论 ===")
    if success:
        print("✅ 算法逻辑正常，应该能检测到重复记录")
        print("❓ 如果在实际应用中看不到结果，可能的原因:")
        print("   1. 用户权限问题 - 确保以admin身份登录")
        print("   2. 数据库连接问题 - 检查应用是否连接到正确的数据库")
        print("   3. 缓存问题 - 尝试清除浏览器缓存或重启应用")
        print("   4. JavaScript错误 - 检查浏览器控制台是否有错误")
        print("   5. API调用失败 - 检查网络请求是否成功")
    else:
        print("❌ 算法逻辑有问题，需要进一步调试")
    
    print("\n下一步建议:")
    print("1. 以admin用户登录应用")
    print("2. 打开客户合并工具")
    print("3. 打开浏览器开发者工具，查看Network和Console选项卡")
    print("4. 点击'开始检测'按钮")
    print("5. 检查API请求是否成功返回数据")
    print("6. 如果有错误，查看服务器日志")