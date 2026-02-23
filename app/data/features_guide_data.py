# -*- coding: utf-8 -*-
"""PMA 新功能说明书数据定义

scenarios 结构：每个场景包含 title、desc、image 三个字段，
用于在说明书中以轮播图形式展示，切换时同步更新截图和说明文字。

数据加载优先级：JSON 文件 > Python 默认值（含 _l() 翻译）
"""
import json
import os

from flask_babel import lazy_gettext as _l

GUIDE_DATA_JSON = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                'scripts', 'temp', 'guide_data.json')


FEATURES_GUIDE_DATA = [
    {
        'id': 'ai-chat',
        'icon': 'smart_toy',
        'color': 'purple',
        'hero_image': 'ai-chat_main.png',
        'title': _l('AI 智能助手'),
        'keywords': [_l('智能对话'), _l('数据查询'), _l('自动翻译'), _l('表单创建')],
        'summary': _l('内置 AI 聊天助手，支持自然语言查询业务数据、自动翻译、辅助创建表单，让日常工作更高效。'),
        'description': [
            _l('PMA 现已集成 AI 智能助手，您可以在系统内直接与 AI 进行对话。无论是查询客户信息、项目进度，还是分析销售数据，只需用自然语言描述需求，AI 即可快速给出答案。'),
            _l('AI 助手支持自动识别对话语言并进行翻译，方便中英文环境下的沟通协作。当您在聊天中 @AI 时，助手会自动参与对话并提供智能回复。'),
            _l('此外，AI 助手还能辅助创建报价单、项目等表单，通过对话式交互引导您完成复杂的数据录入工作。'),
        ],
        'scenarios': [
            {'title': _l('快速查询'), 'desc': _l('用自然语言提问，如"上个月我负责的项目有哪些？"，AI 即时返回结果。'), 'image': 'ai-chat_1.png'},
            {'title': _l('数据分析'), 'desc': _l('询问业务数据指标，如"今年Q1的客户活跃度是多少？"，获取数据洞察。'), 'image': 'ai-chat_2.png'},
            {'title': _l('翻译协助'), 'desc': _l('在中英文对话中自动识别语言并翻译消息内容，跨语言沟通无障碍。'), 'image': 'ai-chat_3.png'},
            {'title': _l('表单创建'), 'desc': _l('通过对话式交互引导创建报价单、项目等表单，简化复杂数据录入。'), 'image': 'ai-chat_4.png'},
        ],
        'entry': _l('点击顶部导航栏右侧的聊天图标，或使用分屏模式打开 AI 面板'),
        'steps': [
            _l('点击导航栏右上角的聊天图标打开聊天面板'),
            _l('在输入框中输入您的问题或需求'),
            _l('AI 会实时流式返回回答，支持 Markdown 格式'),
            _l('如需切换 AI 模型，可在面板顶部选择不同的 AI 提供商'),
        ],
    },
    {
        'id': 'points-system',
        'icon': 'emoji_events',
        'color': 'yellow',
        'hero_image': 'points-system_main.png',
        'title': _l('积分系统'),
        'keywords': [_l('业绩积分'), _l('引用系数'), _l('排行榜'), _l('产品评分')],
        'summary': _l('基于业务贡献的积分激励体系，自动计算报价产品积分，实时显示个人积分排名。'),
        'description': [
            _l('积分系统根据您的业务贡献自动计算积分。每当您创建或更新报价单时，系统会根据报价中产品的引用系数自动计算并记录积分。'),
            _l('每个产品都有对应的积分系数（引用系数），高价值或战略重点产品的系数更高。这意味着推广重点产品能获得更多积分奖励。'),
            _l('积分以年度为周期，您可以在导航栏实时查看当前积分，也可以查看年度积分排行榜，了解自己在团队中的排名。'),
        ],
        'scenarios': [
            {'title': _l('查看积分'), 'desc': _l('导航栏顶部实时显示当前年度积分，随时掌握自己的业绩表现。'), 'image': 'points-system_1.png'},
            {'title': _l('了解排名'), 'desc': _l('查看积分排行榜，了解自己在团队中的位置和差距。'), 'image': 'points-system_2.png'},
            {'title': _l('策略参考'), 'desc': _l('根据产品积分系数选择推广重点，高系数产品带来更多积分奖励。'), 'image': 'points-system_3.png'},
            {'title': _l('业绩激励'), 'desc': _l('积分作为绩效考核的参考指标之一，激励业务积极性。'), 'image': 'points-system_4.png'},
        ],
        'entry': _l('导航栏顶部显示积分徽章，点击可查看积分详情'),
        'steps': [
            _l('在导航栏顶部查看您的当前积分'),
            _l('创建报价单并添加产品，系统自动计算积分'),
            _l('提交报价后积分自动记入您的账户'),
            _l('查看排行榜了解团队积分排名'),
        ],
    },
    {
        'id': 'resource-pool',
        'hero_image': 'resource-pool_main.png',
        'icon': 'lock_open',
        'color': 'blue',
        'title': _l('资源池与访问申请'),
        'keywords': [_l('跨权限搜索'), _l('访问请求'), _l('资源共享'), _l('权限审批')],
        'summary': _l('突破权限边界的资源发现机制，支持跨权限搜索客户资源并发起访问申请。'),
        'description': [
            _l('资源池功能让您能够发现系统中超出个人权限范围的客户资源。当您搜索客户时，除了自己有权访问的数据外，还能看到其他同事管理的客户（以脱敏方式展示）。'),
            _l('如果您发现某个客户与自己的业务相关，可以直接发起访问申请。申请会发送给该客户的负责人审批，审批通过后您即可获得查看权限。'),
            _l('整个流程透明高效，既保护了数据安全，又促进了团队间的资源共享和业务协作。'),
        ],
        'scenarios': [
            {'title': _l('发现潜在客户'), 'desc': _l('搜索时发现其他同事管理的相关客户，锁定图标标识超出权限的资源。'), 'image': 'resource-pool_1.png'},
            {'title': _l('跨部门协作'), 'desc': _l('申请访问其他部门的客户资源，促进联合开发和业务协同。'), 'image': 'resource-pool_2.png'},
            {'title': _l('资源整合'), 'desc': _l('通过搜索发现系统中已有的客户，避免重复录入和资源浪费。'), 'image': 'resource-pool_3.png'},
            {'title': _l('权限管理'), 'desc': _l('客户负责人在线审批他人的访问请求，流程透明可追溯。'), 'image': 'resource-pool_4.png'},
        ],
        'entry': _l('在客户列表页面搜索时，超出权限的结果会显示锁定图标'),
        'steps': [
            _l('在客户搜索框输入关键词进行搜索'),
            _l('搜索结果中带锁定图标的是超出权限的资源'),
            _l('点击锁定图标或"申请访问"按钮发起申请'),
            _l('填写申请理由并提交'),
            _l('等待客户负责人审批，通过后自动获得访问权限'),
        ],
    },
    {
        'id': 'split-screen',
        'hero_image': 'split-screen_main.png',
        'icon': 'view_sidebar',
        'color': 'cyan',
        'title': _l('分屏浏览与消息通知'),
        'keywords': [_l('分屏浏览'), _l('@提醒'), _l('待审批'), _l('待办事项')],
        'summary': _l('50/50 分屏布局支持边聊天边工作，消息通知面板集中显示 @提醒和待办事项。'),
        'description': [
            _l('分屏浏览功能将页面分为左右两半：左侧是聊天面板，右侧是您正在浏览的业务页面。这样您可以一边与同事或 AI 沟通，一边查看客户信息或编辑报价单。'),
            _l('消息通知面板集中展示所有需要您关注的事项：@您的聊天消息、待审批的项目/报销单、即将到期的任务等。点击通知可直接跳转到对应页面。'),
            _l('分屏模式下导航栏会自动收窄，最大化利用屏幕空间。您可以随时切换分屏和全屏模式。'),
        ],
        'scenarios': [
            {'title': _l('边聊边查'), 'desc': _l('与同事讨论项目时同时查看项目详情，信息对照一目了然。'), 'image': 'split-screen_1.png'},
            {'title': _l('AI 辅助'), 'desc': _l('一边使用 AI 助手获取信息，一边填写表单或编辑数据。'), 'image': 'split-screen_2.png'},
            {'title': _l('消息追踪'), 'desc': _l('快速查看和处理 @提醒消息，不错过任何重要沟通。'), 'image': 'split-screen_3.png'},
            {'title': _l('审批处理'), 'desc': _l('在通知面板中快速处理待审批事项，提升审批效率。'), 'image': 'split-screen_4.png'},
        ],
        'entry': _l('点击导航栏的分屏图标切换分屏模式，点击铃铛图标打开消息面板'),
        'steps': [
            _l('点击导航栏右上角的分屏图标进入分屏模式'),
            _l('左侧聊天面板自动展开，右侧显示当前页面'),
            _l('点击铃铛图标查看消息通知面板'),
            _l('点击通知项可直接跳转到对应页面处理'),
        ],
    },
    {
        'id': 'dashboard',
        'hero_image': 'dashboard_main.png',
        'icon': 'dashboard',
        'color': 'green',
        'title': _l('绩效仪表盘增强'),
        'keywords': [_l('目标达成'), _l('活跃度分析'), _l('行业分布'), _l('客户地图')],
        'summary': _l('全面升级的绩效仪表盘，新增目标达成率追踪、客户活跃度分析和行业分布图表。'),
        'description': [
            _l('绩效仪表盘经过全面升级，现在提供更丰富的数据可视化。首页仪表盘展示您的年度目标达成率、月度业绩趋势、客户活跃度等核心指标。'),
            _l('新增的行业分布图表帮助您了解客户的行业构成，发现潜力行业。客户活跃度分析则追踪客户的互动频率，帮助您识别需要重点维护的客户。'),
            _l('仪表盘支持按年份筛选，所有图表均支持交互操作，鼠标悬停可查看详细数据。性能方面进行了大幅优化，加载速度提升显著。'),
        ],
        'scenarios': [
            {'title': _l('业绩追踪'), 'desc': _l('实时查看年度/月度目标达成率，掌握业绩进展。'), 'image': 'dashboard_1.png'},
            {'title': _l('趋势分析'), 'desc': _l('查看月度业绩趋势变化曲线，发现增长或下滑趋势。'), 'image': 'dashboard_2.png'},
            {'title': _l('客户分析'), 'desc': _l('了解客户的行业分布和活跃度，识别重点维护对象。'), 'image': 'dashboard_3.png'},
            {'title': _l('管理决策'), 'desc': _l('基于数据图表制定业务策略，数据驱动科学决策。'), 'image': 'dashboard_4.png'},
        ],
        'entry': _l('登录后首页即为绩效仪表盘，或点击导航栏"仪表盘"'),
        'steps': [
            _l('登录系统后自动进入绩效仪表盘首页'),
            _l('使用顶部年份选择器切换查看不同年份的数据'),
            _l('点击各图表区域可查看详细数据'),
            _l('鼠标悬停在图表元素上查看具体数值'),
        ],
    },
    {
        'id': 'task-management',
        'hero_image': 'task-management_main.png',
        'icon': 'task_alt',
        'color': 'orange',
        'title': _l('任务管理系统'),
        'keywords': [_l('待办任务'), _l('日历关联'), _l('附件管理'), _l('协作评论')],
        'summary': _l('轻量级任务管理，支持创建任务、设定截止日期、上传附件和协作评论。'),
        'description': [
            _l('任务管理系统帮助您高效管理日常工作事项。您可以创建任务、设定优先级和截止日期，并将任务关联到具体的项目或客户。'),
            _l('每个任务支持上传附件和添加评论，方便团队协作。任务状态包括待办、进行中和已完成，一目了然。'),
            _l('任务与日历系统关联，即将到期的任务会在消息通知面板中提醒，确保不遗漏任何重要事项。'),
        ],
        'scenarios': [
            {'title': _l('日常管理'), 'desc': _l('创建每日待办事项并跟踪完成情况，高效管理工作节奏。'), 'image': 'task-management_1.png'},
            {'title': _l('项目协作'), 'desc': _l('为项目创建关联任务并分配给团队成员，协同推进工作。'), 'image': 'task-management_2.png'},
            {'title': _l('文件管理'), 'desc': _l('在任务中附加相关文档和资料，信息集中不遗漏。'), 'image': 'task-management_3.png'},
            {'title': _l('进度追踪'), 'desc': _l('查看任务完成率了解整体进度，及时发现延期风险。'), 'image': 'task-management_4.png'},
        ],
        'entry': _l('点击导航栏的"任务管理"菜单项进入任务列表'),
        'steps': [
            _l('进入任务管理页面，查看当前任务列表'),
            _l('点击"新建任务"创建新的待办事项'),
            _l('设置任务标题、描述、优先级和截止日期'),
            _l('可选择关联到具体项目或客户'),
            _l('添加附件或评论与团队协作'),
        ],
    },
    {
        'id': 'file-manager',
        'hero_image': 'file-manager_main.png',
        'icon': 'folder_open',
        'color': 'indigo',
        'title': _l('文件管理系统'),
        'keywords': [_l('文件存储'), _l('去重管理'), _l('知识库'), _l('快速上传')],
        'summary': _l('统一的文件存储和管理平台，支持文件去重、分类管理和知识库建设。'),
        'description': [
            _l('文件管理系统为您提供统一的文件存储平台。上传的发票、合同、产品资料等文件自动归类，支持按类型、日期和关联对象筛选查找。'),
            _l('系统内置文件去重机制，相同文件不会重复存储，节省存储空间。支持常见的文档、图片和 PDF 格式文件。'),
            _l('知识库功能让您可以将重要的产品资料、行业报告等文档集中管理，形成团队共享的知识资产。'),
        ],
        'scenarios': [
            {'title': _l('文件归档'), 'desc': _l('上传发票、合同等商务文件，系统自动归类整理。'), 'image': 'file-manager_1.png'},
            {'title': _l('资料查找'), 'desc': _l('按类型或关联对象快速查找历史文件，秒级定位。'), 'image': 'file-manager_2.png'},
            {'title': _l('知识沉淀'), 'desc': _l('将产品手册、行业报告等上传到知识库，形成团队共享资产。'), 'image': 'file-manager_3.png'},
            {'title': _l('空间优化'), 'desc': _l('文件去重机制自动识别重复文件，节省存储空间。'), 'image': 'file-manager_4.png'},
        ],
        'entry': _l('点击导航栏的"文件管理"菜单项进入文件列表'),
        'steps': [
            _l('进入文件管理页面查看已上传的文件列表'),
            _l('点击"上传文件"或拖拽文件到上传区域'),
            _l('选择文件分类和关联对象（如客户、项目）'),
            _l('使用搜索和筛选功能快速查找所需文件'),
        ],
    },
    {
        'id': 'customer-map',
        'hero_image': 'customer-map_main.png',
        'icon': 'map',
        'color': 'red',
        'title': _l('客户地图'),
        'keywords': [_l('地图可视化'), _l('区域分布'), _l('客户定位'), _l('地理筛选')],
        'summary': _l('基于地理位置的客户分布可视化，支持省份级别的客户数据地图展示。'),
        'description': [
            _l('客户地图功能将您的客户数据以地图的形式直观展示。中国地图上以不同颜色深浅表示各省份的客户数量，一眼即可看出客户集中的区域。'),
            _l('点击地图上的省份可以查看该地区的客户详细列表，支持从地图视角快速定位和管理客户。'),
            _l('结合地理筛选功能，您可以按区域分析客户分布特征，发现空白市场和机会区域，为市场拓展提供数据支持。'),
        ],
        'scenarios': [
            {'title': _l('区域分析'), 'desc': _l('直观查看客户在全国各省的分布情况，颜色深浅代表客户密度。'), 'image': 'customer-map_1.png'},
            {'title': _l('市场发现'), 'desc': _l('识别客户稀少的区域作为潜在市场，发现拓展机会。'), 'image': 'customer-map_2.png'},
            {'title': _l('快速定位'), 'desc': _l('通过地图点击快速查看某地区的客户列表，高效管理。'), 'image': 'customer-map_3.png'},
            {'title': _l('战略规划'), 'desc': _l('基于地理分布制定区域营销策略，精准投放资源。'), 'image': 'customer-map_4.png'},
        ],
        'entry': _l('在客户列表页面点击"地图视图"切换按钮'),
        'steps': [
            _l('进入客户列表页面'),
            _l('点击"地图视图"切换按钮进入地图模式'),
            _l('查看中国地图上的客户分布热力图'),
            _l('点击具体省份查看该区域客户列表'),
        ],
    },
]


def _serialize_defaults():
    """将默认数据中的 _l() LazyString 转为纯字符串"""
    result = []
    for feat in FEATURES_GUIDE_DATA:
        item = {
            'id': feat['id'], 'icon': feat['icon'], 'color': feat['color'],
            'hero_image': feat.get('hero_image', ''),
            'title': str(feat['title']),
            'keywords': [str(k) for k in feat.get('keywords', [])],
            'summary': str(feat.get('summary', '')),
            'description': [str(p) for p in feat['description']] if isinstance(feat['description'], list) else [str(feat['description'])],
            'scenarios': [{'title': str(s['title']), 'desc': str(s['desc']), 'image': s['image']} for s in feat.get('scenarios', [])],
            'entry': str(feat.get('entry', '')),
            'steps': [str(s) for s in feat.get('steps', [])],
        }
        result.append(item)
    return result


def get_features_data():
    """加载说明书数据：优先 JSON 文件，否则用 Python 默认值"""
    if os.path.isfile(GUIDE_DATA_JSON):
        with open(GUIDE_DATA_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    return _serialize_defaults()


def save_features_data(data):
    """保存说明书数据到 JSON"""
    os.makedirs(os.path.dirname(GUIDE_DATA_JSON), exist_ok=True)
    with open(GUIDE_DATA_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
