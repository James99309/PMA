#!/usr/bin/env python3
"""
迁移文件解析器
负责解析迁移文件，构建迁移依赖图，找到正确的迁移路径

核心功能：
1. 解析所有迁移文件的revision和down_revision信息
2. 构建迁移依赖有向图
3. 识别合并迁移并评估安全性
4. 计算从起始版本到目标版本的线性路径
"""

import os
import re
import ast
import logging
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, deque

class MigrationInfo:
    """迁移信息数据结构"""
    def __init__(self, filepath: str, revision: str, down_revision, filename: str):
        self.filepath = filepath
        self.revision = revision
        self.down_revision = down_revision
        self.filename = filename
        self.is_merge = False
        self.has_real_operations = False
        self.description = ""
        
        # 获取文件修改时间
        try:
            self.file_path_mtime = os.path.getmtime(filepath)
        except:
            self.file_path_mtime = 0
        
        # 分析down_revision类型
        if isinstance(down_revision, tuple):
            self.is_merge = True
        elif isinstance(down_revision, list) and len(down_revision) > 1:
            self.is_merge = True
            
    def __str__(self):
        return f"Migration({self.revision[:8]}..., {self.filename})"
        
    def __repr__(self):
        return self.__str__()

class MigrationParser:
    """迁移文件解析器"""
    
    def __init__(self, migrations_dir: str):
        self.migrations_dir = migrations_dir
        self.logger = logging.getLogger('MigrationParser')
        self.migrations: Dict[str, MigrationInfo] = {}
        self.dependency_graph: Dict[str, List[str]] = defaultdict(list)
        self.reverse_graph: Dict[str, List[str]] = defaultdict(list)
        
    def parse_all_migrations(self) -> Dict[str, MigrationInfo]:
        """解析所有迁移文件"""
        self.logger.info("📂 开始解析迁移文件...")
        
        versions_dir = os.path.join(self.migrations_dir, 'versions')
        if not os.path.exists(versions_dir):
            self.logger.error(f"迁移目录不存在: {versions_dir}")
            return {}
        
        migration_files = [f for f in os.listdir(versions_dir) if f.endswith('.py')]
        self.logger.info(f"发现 {len(migration_files)} 个迁移文件")
        
        for filename in migration_files:
            filepath = os.path.join(versions_dir, filename)
            migration_info = self._parse_single_file(filepath, filename)
            if migration_info:
                self.migrations[migration_info.revision] = migration_info
        
        self._build_dependency_graph()
        self._analyze_operations()
        
        self.logger.info(f"✅ 解析完成: {len(self.migrations)} 个有效迁移")
        self._log_migration_summary()
        
        return self.migrations
    
    def _parse_single_file(self, filepath: str, filename: str) -> Optional[MigrationInfo]:
        """解析单个迁移文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取revision信息
            revision_match = re.search(r"revision\s*=\s*['\"]([^'\"]+)['\"]", content)
            down_revision_match = re.search(r"down_revision\s*=\s*(.+)", content)
            
            if not revision_match:
                self.logger.warning(f"无法提取revision: {filename}")
                return None
                
            revision = revision_match.group(1)
            
            # 解析down_revision
            down_revision = None
            if down_revision_match:
                down_revision_str = down_revision_match.group(1).strip()
                if down_revision_str == 'None':
                    down_revision = None
                elif down_revision_str.startswith('(') and down_revision_str.endswith(')'):
                    # 元组形式的down_revision - 合并迁移
                    try:
                        down_revision = ast.literal_eval(down_revision_str)
                    except:
                        # 如果解析失败，尝试手动解析
                        down_revision = self._parse_tuple_manually(down_revision_str)
                elif down_revision_str.startswith('[') and down_revision_str.endswith(']'):
                    # 列表形式
                    try:
                        down_revision = ast.literal_eval(down_revision_str)
                    except:
                        down_revision = self._parse_list_manually(down_revision_str)
                else:
                    # 单个字符串
                    down_revision = down_revision_str.strip('\'"')
            
            # 提取描述
            description_match = re.search(r'"""([^"]+)"""', content)
            description = description_match.group(1).strip() if description_match else ""
            
            migration_info = MigrationInfo(filepath, revision, down_revision, filename)
            migration_info.description = description
            
            return migration_info
            
        except Exception as e:
            self.logger.error(f"解析文件失败 {filename}: {e}")
            return None
    
    def _parse_tuple_manually(self, tuple_str: str) -> Tuple[str, ...]:
        """手动解析元组字符串"""
        # 移除括号和空格
        content = tuple_str.strip('() ')
        if not content:
            return ()
        
        # 分割并清理
        items = []
        for item in content.split(','):
            item = item.strip().strip('\'"')
            if item:
                items.append(item)
        
        return tuple(items)
    
    def _parse_list_manually(self, list_str: str) -> List[str]:
        """手动解析列表字符串"""
        # 移除方括号和空格
        content = list_str.strip('[] ')
        if not content:
            return []
        
        # 分割并清理
        items = []
        for item in content.split(','):
            item = item.strip().strip('\'"')
            if item:
                items.append(item)
        
        return items
    
    def _build_dependency_graph(self):
        """构建迁移依赖图"""
        self.logger.info("🔗 构建迁移依赖图...")
        
        for revision, migration in self.migrations.items():
            if migration.down_revision is None:
                continue
                
            if isinstance(migration.down_revision, (tuple, list)):
                # 合并迁移 - 依赖多个父迁移
                for parent in migration.down_revision:
                    if parent and parent in self.migrations:
                        self.dependency_graph[parent].append(revision)
                        self.reverse_graph[revision].append(parent)
            else:
                # 普通迁移 - 依赖单个父迁移
                parent = migration.down_revision
                if parent and parent in self.migrations:
                    self.dependency_graph[parent].append(revision)
                    self.reverse_graph[revision].append(parent)
    
    def _analyze_operations(self):
        """分析迁移是否包含实际的数据库操作"""
        self.logger.info("🔍 分析迁移操作...")
        
        for revision, migration in self.migrations.items():
            try:
                with open(migration.filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 查找upgrade函数
                upgrade_match = re.search(r'def upgrade\(\):(.*?)(?=def\s|\Z)', content, re.DOTALL)
                if upgrade_match:
                    upgrade_content = upgrade_match.group(1)
                    
                    # 检查是否有实际操作
                    has_operations = self._has_real_database_operations(upgrade_content)
                    migration.has_real_operations = has_operations
                    
                    if migration.is_merge and not has_operations:
                        self.logger.debug(f"🔄 纯合并迁移: {migration.revision[:8]}... ({migration.filename})")
                    elif migration.is_merge and has_operations:
                        self.logger.warning(f"⚠️  危险合并迁移: {migration.revision[:8]}... ({migration.filename})")
                        
            except Exception as e:
                self.logger.warning(f"分析操作失败 {migration.filename}: {e}")
    
    def _has_real_database_operations(self, upgrade_content: str) -> bool:
        """检查升级函数是否包含实际的数据库操作"""
        # 移除注释和空行
        lines = [line.strip() for line in upgrade_content.split('\n') if line.strip()]
        
        # 过滤掉pass、注释和空行
        meaningful_lines = []
        for line in lines:
            if (line == 'pass' or 
                line.startswith('#') or 
                line.startswith('"""') or
                line.startswith("'''") or
                not line):
                continue
            meaningful_lines.append(line)
        
        # 检查是否有数据库操作关键字
        db_operations = ['op.', 'batch_op.', 'connection.execute', 'sa.', 'create_table', 'drop_table', 
                        'add_column', 'drop_column', 'alter_column', 'create_index', 'drop_index']
        
        for line in meaningful_lines:
            if any(op in line for op in db_operations):
                return True
        
        return False
    
    def find_migration_path(self, start_revision: str, target_revision: str) -> List[str]:
        """找到从起始版本到目标版本的迁移路径"""
        self.logger.info(f"🛤️  查找迁移路径: {start_revision[:8]}... -> {target_revision[:8]}...")
        
        if start_revision == target_revision:
            return []
        
        # 使用BFS找到最短路径
        queue = deque([(start_revision, [])])  # 路径不包含起始节点
        visited = {start_revision}
        
        while queue:
            current_revision, path = queue.popleft()
            
            # 检查当前节点的所有子节点
            for next_revision in self.dependency_graph.get(current_revision, []):
                new_path = path + [next_revision]
                
                if next_revision == target_revision:
                    # 找到目标，返回路径
                    self.logger.info(f"✅ 找到迁移路径: {len(new_path)} 步")
                    self._log_migration_path(new_path)
                    return new_path
                
                if next_revision not in visited:
                    visited.add(next_revision)
                    queue.append((next_revision, new_path))
        
        # 如果BFS没有找到路径，尝试直接检查依赖链
        self.logger.warning("BFS未找到路径，尝试直接检查依赖链...")
        direct_path = self._find_direct_dependency_chain(start_revision, target_revision)
        
        if direct_path:
            self.logger.info(f"✅ 找到直接依赖路径: {len(direct_path)} 步")
            self._log_migration_path(direct_path)
            return direct_path
        
        # 没有找到路径
        self.logger.error(f"❌ 无法找到从 {start_revision} (head) 到 {target_revision} 的迁移路径")
        return []
        
    def _find_direct_dependency_chain(self, start_revision: str, target_revision: str) -> List[str]:
        """直接通过依赖链查找路径"""
        path = []
        current = start_revision
        visited = set()
        
        while current and current != target_revision and current not in visited:
            visited.add(current)
            
            # 查找依赖于当前版本的迁移
            next_revisions = self.dependency_graph.get(current, [])
            
            if len(next_revisions) == 1:
                # 单一路径，继续跟踪
                next_revision = next_revisions[0]
                path.append(next_revision)
                current = next_revision
            elif len(next_revisions) > 1:
                # 多个分支，选择通往目标的分支
                found_next = None
                for next_revision in next_revisions:
                    if self._leads_to_target(next_revision, target_revision, visited.copy()):
                        found_next = next_revision
                        break
                        
                if found_next:
                    path.append(found_next)
                    current = found_next
                else:
                    break
            else:
                # 没有下一步
                break
                
        return path if current == target_revision else []
        
    def _leads_to_target(self, start: str, target: str, visited: set, max_depth: int = 10) -> bool:
        """检查从start是否能到达target"""
        if max_depth <= 0 or start in visited:
            return False
            
        if start == target:
            return True
            
        visited.add(start)
        for next_revision in self.dependency_graph.get(start, []):
            if self._leads_to_target(next_revision, target, visited.copy(), max_depth - 1):
                return True
                
        return False
    
    def filter_safe_migrations(self, migration_path: List[str]) -> List[str]:
        """过滤掉不安全的合并迁移"""
        self.logger.info("🔒 过滤安全迁移...")
        
        safe_path = []
        skipped_merges = []
        
        for revision in migration_path:
            migration = self.migrations.get(revision)
            if not migration:
                continue
            
            if migration.is_merge and not migration.has_real_operations:
                # 纯合并迁移 - 可以跳过
                skipped_merges.append(revision)
                self.logger.info(f"🔄 跳过纯合并: {revision[:8]}... ({migration.filename})")
            elif migration.is_merge and migration.has_real_operations:
                # 危险合并迁移 - 警告但包含
                self.logger.warning(f"⚠️  危险合并迁移: {revision[:8]}... ({migration.filename})")
                self.logger.warning("   此迁移包含实际数据库操作，无法跳过")
                safe_path.append(revision)
            else:
                # 普通迁移 - 包含
                safe_path.append(revision)
        
        if skipped_merges:
            self.logger.info(f"✅ 跳过了 {len(skipped_merges)} 个纯合并迁移")
        
        return safe_path
    
    def get_migration_info(self, revision: str) -> Optional[MigrationInfo]:
        """获取指定迁移的信息"""
        return self.migrations.get(revision)
    
    def get_merge_migrations(self) -> List[MigrationInfo]:
        """获取所有合并迁移"""
        return [migration for migration in self.migrations.values() if migration.is_merge]
    
    def get_dangerous_merges(self) -> List[MigrationInfo]:
        """获取包含实际操作的危险合并迁移"""
        return [migration for migration in self.migrations.values() 
                if migration.is_merge and migration.has_real_operations]
    
    def _log_migration_summary(self):
        """记录迁移摘要信息"""
        total = len(self.migrations)
        merges = len(self.get_merge_migrations())
        dangerous = len(self.get_dangerous_merges())
        
        self.logger.info(f"📊 迁移摘要:")
        self.logger.info(f"   总迁移数: {total}")
        self.logger.info(f"   合并迁移: {merges}")
        self.logger.info(f"   危险合并: {dangerous}")
        
        if dangerous > 0:
            self.logger.warning("⚠️  发现危险合并迁移，需要特别小心")
    
    def _log_migration_path(self, migration_path: List[str]):
        """记录迁移路径详情"""
        self.logger.info(f"📋 迁移路径 ({len(migration_path)} 步):")
        for i, revision in enumerate(migration_path, 1):
            migration = self.migrations.get(revision)
            if migration:
                status = "🔄 合并" if migration.is_merge else "➡️  普通"
                ops = "有操作" if migration.has_real_operations else "无操作"
                self.logger.info(f"   {i:2d}. {status} {revision[:8]}... ({ops}) - {migration.filename}")
            else:
                self.logger.info(f"   {i:2d}. ❓ {revision[:8]}... (未知)")