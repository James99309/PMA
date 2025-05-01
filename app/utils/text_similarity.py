"""
项目名称相似度比较工具

此模块提供了专门针对中文项目名称的相似度计算函数，结合了以下几种方法：
1. 字符级别的编辑距离相似度 (Levenshtein)
2. 基于jieba分词的关键词匹配
3. 处理常见的中文项目命名模式

相比传统的fuzzywuzzy，此模块更适合中文项目名称的相似度比较
"""

import re
import jieba
from fuzzywuzzy import fuzz
import logging

logger = logging.getLogger(__name__)

# 行业关键词权重表
INDUSTRY_KEYWORDS = {
    "半导体": 1.5,
    "数据中心": 1.5,
    "实验室": 1.3,
    "工厂": 1.3,
    "生产基地": 1.3,
    "厂房": 1.3,
    "园区": 1.2,
    "楼": 1.2,
    "基地": 1.2,
}

# 中国省市名称列表（部分常见地名）
LOCATION_NAMES = [
    "北京", "上海", "广州", "深圳", "杭州", "南京", "成都", "重庆", "武汉", "西安",
    "天津", "苏州", "厦门", "长沙", "青岛", "宁波", "郑州", "大连", "沈阳", "济南",
]

def clean_project_name(name):
    """清理项目名称，去除特殊字符和多余空格"""
    if not name:
        return ""
    # 替换特殊字符为空格
    name = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', name)
    # 替换多个空格为单个空格
    name = re.sub(r'\s+', ' ', name)
    return name.strip().lower()

def get_keywords(name):
    """使用jieba分词提取项目名称中的关键词"""
    # 先清理名称
    clean_name = clean_project_name(name)
    # 使用jieba分词
    words = jieba.cut(clean_name)
    # 过滤掉停用词和单个字符
    keywords = [word for word in words if len(word) > 1]
    return keywords

def calculate_keyword_similarity(name1, name2):
    """计算基于关键词的相似度"""
    keywords1 = set(get_keywords(name1))
    keywords2 = set(get_keywords(name2))
    
    if not keywords1 or not keywords2:
        return 0
    
    # 计算关键词的交集和并集
    intersection = keywords1.intersection(keywords2)
    union = keywords1.union(keywords2)
    
    # Jaccard相似系数
    if len(union) == 0:
        return 0
    
    return len(intersection) / len(union) * 100

def calculate_chinese_similarity(str1, str2, debug=False):
    """
    计算两个中文项目名称的相似度，针对中文项目命名特点进行了优化
    
    参数:
    str1, str2: 要比较的两个字符串
    debug: 是否输出调试信息
    
    返回:
    float: 相似度百分比 (0-100)
    """
    if not str1 or not str2:
        return 0
        
    # 进行必要的预处理
    str1 = str1.strip()
    str2 = str2.strip()
    
    # 1. 基础相似度 (编辑距离)
    base_similarity = fuzz.ratio(str1, str2)
    
    # 2. 分词后的关键词匹配
    words1 = set(jieba.cut(str1))
    words2 = set(jieba.cut(str2))
    
    # 计算关键词重叠率
    common_words = words1.intersection(words2)
    if not common_words:
        keyword_ratio = 0
    else:
        all_words = words1.union(words2)
        keyword_ratio = len(common_words) / len(all_words) * 100
    
    # 3. 检查是否包含相同的地名
    location_bonus = 0
    common_locations = []
    for location in LOCATION_NAMES:
        if location in str1 and location in str2:
            common_locations.append(location)
            location_bonus += 10  # 每有一个相同地名加10分
    
    # 4. 检查行业关键词
    industry_bonus = 0
    common_industries = []
    for keyword, weight in INDUSTRY_KEYWORDS.items():
        if keyword in str1 and keyword in str2:
            common_industries.append(keyword)
            industry_bonus += 15 * weight  # 每有一个相同行业关键词加权
    
    # 特殊处理：如果包含"半导体"关键词，给予额外权重
    if "半导体" in common_industries:
        industry_bonus += 5
    
    # 5. 短语匹配 (找出最长公共子串)
    def find_longest_common_substring(s1, s2):
        m = [[0] * (1 + len(s2)) for _ in range(1 + len(s1))]
        longest, x_longest = 0, 0
        for x in range(1, 1 + len(s1)):
            for y in range(1, 1 + len(s2)):
                if s1[x - 1] == s2[y - 1]:
                    m[x][y] = m[x - 1][y - 1] + 1
                    if m[x][y] > longest:
                        longest = m[x][y]
                        x_longest = x
                else:
                    m[x][y] = 0
        return s1[x_longest - longest: x_longest]
    
    common_substring = find_longest_common_substring(str1, str2)
    substring_bonus = 0
    if len(common_substring) > 1:  # 至少要有2个字符
        substring_bonus = len(common_substring) / max(len(str1), len(str2)) * 20
    
    # 计算最终相似度，采用加权平均
    final_similarity = (
        base_similarity * 0.4 +  # 编辑距离占40%
        keyword_ratio * 0.3 +    # 关键词匹配占30%
        location_bonus +         # 地名奖励
        industry_bonus +         # 行业关键词奖励
        substring_bonus          # 公共子串奖励
    )
    
    # 结果限制在0-100之间
    final_similarity = max(0, min(100, final_similarity))
    
    # 输出调试信息
    if debug:
        print(f"比较: '{str1}' 与 '{str2}'")
        print(f"基础相似度(编辑距离): {base_similarity:.2f}")
        print(f"关键词: {words1} vs {words2}")
        print(f"共同关键词: {common_words}")
        print(f"关键词匹配率: {keyword_ratio:.2f}")
        print(f"共同地名: {common_locations}")
        print(f"地名奖励: {location_bonus}")
        print(f"共同行业关键词: {common_industries}")
        print(f"行业关键词奖励: {industry_bonus}")
        print(f"最长公共子串: '{common_substring}'")
        print(f"子串奖励: {substring_bonus:.2f}")
        print(f"最终相似度: {final_similarity:.2f}")
    
    return final_similarity

def is_similar_project_name(str1, str2, threshold=60, debug=False):
    """
    判断两个项目名称是否相似
    
    参数:
    str1, str2: 要比较的两个字符串
    threshold: 相似度阈值，默认为60
    debug: 是否输出调试信息
    
    返回:
    bool: 是否相似
    float: 相似度分数
    """
    similarity = calculate_chinese_similarity(str1, str2, debug)
    return similarity >= threshold, similarity 