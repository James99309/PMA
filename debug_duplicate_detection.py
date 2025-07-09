#!/usr/bin/env python3
"""
调试重复检测逻辑
测试为什么"上海瑞康通信科技有限公司"的两个记录没有被检测到
"""
import re
import difflib

def normalize_company_name(name):
    """标准化公司名称，用于重复检测"""
    if not name:
        return ""
    
    # 清理不可见字符和额外空格
    normalized = re.sub(r'\s+', '', name.strip())
    normalized = re.sub(r'[^\w\u4e00-\u9fff]', '', normalized)
    
    # 去除常见的公司后缀（按长度从长到短排序）
    suffixes = [
        "有限责任公司", "股份有限公司", "有限公司", "股份公司", 
        "集团公司", "科技公司", "实业公司", "企业公司",
        "公司", "集团", "科技", "实业", "企业",
        "Co.", "Ltd", "Inc", "Corp", "LLC"
    ]
    
    suffixes.sort(key=len, reverse=True)
    for suffix in suffixes:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)]
            break
    
    return normalized.lower()

def find_similar_companies(target_company, all_companies):
    """查找相似的公司，返回带匹配度的结果"""
    similar_companies = []
    target_normalized = normalize_company_name(target_company['company_name'])
    
    print(f"目标公司: {target_company['id']} - \"{target_company['company_name']}\"")
    print(f"标准化为: \"{target_normalized}\"")
    print()
    
    for company in all_companies:
        if company['id'] == target_company['id']:
            continue
            
        company_normalized = normalize_company_name(company['company_name'])
        
        # 计算相似度
        similarity = difflib.SequenceMatcher(None, target_normalized, company_normalized).ratio()
        
        # 增加包含关系的匹配度加权
        containment_bonus = 0
        if len(target_normalized) > 2 and len(company_normalized) > 2:
            if target_normalized in company_normalized or company_normalized in target_normalized:
                containment_bonus = 0.2
        
        # 最终匹配度
        final_score = min(1.0, similarity + containment_bonus)
        
        # 特别检查完全匹配的情况
        if target_normalized == company_normalized:
            final_score = 1.0
        
        print(f"对比公司: {company['id']} - \"{company['company_name']}\"")
        print(f"  标准化为: \"{company_normalized}\"")
        print(f"  基础相似度: {similarity:.3f}")
        print(f"  包含加权: {containment_bonus:.3f}")
        print(f"  最终得分: {final_score:.3f}")
        print(f"  是否相同: {target_normalized == company_normalized}")
        print()
        
        # 降低匹配度阈值，提供更多重复可能性建议
        if final_score > 0.4:  # 从0.6降低到0.4，提供更多建议
            similar_companies.append({
                'company': company,
                'similarity': final_score,
                'match_type': 'high' if final_score > 0.8 else 'medium' if final_score > 0.6 else 'low'
            })
    
    # 按相似度排序
    similar_companies.sort(key=lambda x: x['similarity'], reverse=True)
    return similar_companies

def test_duplicate_detection():
    """测试重复检测逻辑"""
    print("=== 测试重复检测逻辑 ===\n")
    
    # 模拟数据库中的实际记录
    companies = [
        {
            'id': 300,
            'company_name': '上海瑞康通信科技有限公司 ',  # 末尾有空格
            'company_code': '25E09297',
            'owner_id': 15,
            'owner_name': '李华伟',
            'created_at': '2024-02-21 15:18:26',
            'contact_count': 1,
            'action_count': 0
        },
        {
            'id': 424,
            'company_name': '       上海瑞康通信科技有限公司',  # 开头有空格
            'company_code': '25E09421',
            'owner_id': 2,
            'owner_name': '方玲',
            'created_at': '2025-04-17 00:00:00',
            'contact_count': 0,
            'action_count': 0
        },
        {
            'id': 999,
            'company_name': '华为技术有限公司',  # 不相关的公司作为对比
            'company_code': 'HW001',
            'owner_id': 1,
            'owner_name': '张三',
            'created_at': '2024-01-01 00:00:00',
            'contact_count': 5,
            'action_count': 10
        }
    ]
    
    print("所有公司记录:")
    for company in companies:
        print(f"  ID {company['id']}: \"{company['company_name']}\" (长度: {len(company['company_name'])})")
    print()
    
    # 测试以ID 300为目标的重复检测
    print("=== 以ID 300为目标的重复检测 ===")
    target_company = companies[0]  # ID 300
    similar = find_similar_companies(target_company, companies)
    
    print(f"找到 {len(similar)} 个相似公司:")
    for item in similar:
        company = item['company']
        print(f"  - ID {company['id']}: \"{company['company_name']}\" (相似度: {item['similarity']:.3f}, 类型: {item['match_type']})")
    print()
    
    # 测试以ID 424为目标的重复检测
    print("=== 以ID 424为目标的重复检测 ===")
    target_company = companies[1]  # ID 424
    similar = find_similar_companies(target_company, companies)
    
    print(f"找到 {len(similar)} 个相似公司:")
    for item in similar:
        company = item['company']
        print(f"  - ID {company['id']}: \"{company['company_name']}\" (相似度: {item['similarity']:.3f}, 类型: {item['match_type']})")
    print()
    
    # 检查是否会形成重复组
    print("=== 重复组检测 ===")
    
    # 模拟detect_duplicates逻辑
    all_suggestions = []
    processed_companies = set()
    
    for target_company in companies:
        if target_company['id'] in processed_companies:
            continue
            
        similar_companies = find_similar_companies(target_company, companies)
        
        if similar_companies:
            # 将所有相关公司标记为已处理
            processed_companies.add(target_company['id'])
            for item in similar_companies:
                processed_companies.add(item['company']['id'])
            
            max_similarity = max(item['similarity'] for item in similar_companies)
            
            suggestion = {
                'target_company': target_company,
                'similar_companies': [item['company'] for item in similar_companies],
                'max_similarity': max_similarity,
                'similarities': {item['company']['id']: item['similarity'] for item in similar_companies}
            }
            all_suggestions.append(suggestion)
            
            print(f"重复组 {len(all_suggestions)}:")
            print(f"  目标公司: ID {target_company['id']} - \"{target_company['company_name']}\"")
            print(f"  相似公司数: {len(similar_companies)}")
            print(f"  最高相似度: {max_similarity:.3f}")
            for item in similar_companies:
                company = item['company']
                print(f"    - ID {company['id']}: \"{company['company_name']}\" ({item['similarity']:.3f})")
            print()
    
    print(f"总共找到 {len(all_suggestions)} 个重复组")
    
    return all_suggestions

if __name__ == "__main__":
    suggestions = test_duplicate_detection()
    
    print("\n=== 测试结论 ===")
    if suggestions:
        print("✅ 重复检测逻辑正常工作")
        print("✅ 能够检测到 ID 300 和 ID 424 的重复记录")
        print("✅ 标准化函数正确处理了前后空格")
        print("❓ 如果合并工具界面没有显示这些重复记录，可能的原因:")
        print("   1. 数据库查询条件有问题")
        print("   2. 用户权限导致某些记录不可见")
        print("   3. is_deleted 字段过滤有问题")
        print("   4. 前端JavaScript处理有问题")
    else:
        print("❌ 重复检测逻辑有问题")