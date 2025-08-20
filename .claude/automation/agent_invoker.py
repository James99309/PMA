#!/usr/bin/env python3
"""
代理调用器 - 自动代理调用机制
用于自动触发和管理function-lifecycle-manager代理
"""

import os
import json
import subprocess
import sys
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import tempfile
import threading
from queue import Queue, Empty


class AgentInvoker:
    """代理调用器"""
    
    def __init__(self, config_path: str = None, project_root: str = None):
        """初始化代理调用器"""
        self.project_root = project_root or os.getcwd()
        self.config_path = config_path or os.path.join(self.project_root, ".claude/automation/agent-automation.json")
        
        self.config = self._load_config()
        self.logger = self._setup_logger()
        
        # 状态管理
        self.running_tasks = {}
        self.task_queue = Queue()
        self.max_concurrent = self.config.get('global_settings', {}).get('max_concurrent_agents', 3)
        self.timeout = self.config.get('global_settings', {}).get('timeout_seconds', 300)
        
        # 输出目录
        self.reports_dir = os.path.join(self.project_root, '.claude/reports/function-analysis')
        self.cache_dir = os.path.join(self.project_root, '.claude/cache')
        self.logs_dir = os.path.join(self.project_root, '.claude/logs')
        
        self._ensure_directories()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"配置文件未找到: {self.config_path}")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"配置文件格式错误: {e}")
            return {}
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('AgentInvoker')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # 文件处理器
            log_file = os.path.join(self.project_root, '.claude/logs/agent_invoker.log')
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            
            # 控制台处理器  
            console_handler = logging.StreamHandler()
            
            # 格式化器
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        for dir_path in [self.reports_dir, self.cache_dir, self.logs_dir]:
            os.makedirs(dir_path, exist_ok=True)
    
    def is_agent_enabled(self, agent_name: str) -> bool:
        """检查代理是否启用"""
        agent_config = self.config.get('rules', {}).get(agent_name, {})
        return agent_config.get('enabled', False)
    
    def get_trigger_conditions(self, agent_name: str, trigger_type: str) -> Dict[str, Any]:
        """获取触发条件"""
        agent_config = self.config.get('rules', {}).get(agent_name, {})
        triggers = agent_config.get('triggers', {})
        return triggers.get(trigger_type, {})
    
    def should_trigger_agent(self, agent_name: str, trigger_type: str, context: Dict[str, Any]) -> bool:
        """判断是否应该触发代理"""
        if not self.is_agent_enabled(agent_name):
            self.logger.debug(f"代理 {agent_name} 未启用")
            return False
        
        trigger_config = self.get_trigger_conditions(agent_name, trigger_type)
        if not trigger_config.get('enabled', False):
            self.logger.debug(f"触发器 {trigger_type} 未启用")
            return False
        
        conditions = trigger_config.get('conditions', [])
        return self._evaluate_conditions(conditions, context)
    
    def _evaluate_conditions(self, conditions: List[str], context: Dict[str, Any]) -> bool:
        """评估触发条件"""
        for condition in conditions:
            if not self._check_condition(condition, context):
                self.logger.debug(f"条件未满足: {condition}")
                return False
        return True
    
    def _check_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """检查单个条件"""
        # 实现具体的条件检查逻辑
        if condition == "file_contains_new_function":
            return context.get('new_functions_count', 0) > 0
        elif condition == "file_extension_in_python_or_js":
            file_path = context.get('file_path', '')
            return file_path.endswith(('.py', '.js', '.ts'))
        elif condition == "function_signature_changed":
            return context.get('modified_functions_count', 0) > 0
        elif condition == "function_body_modified":
            return context.get('modified_functions_count', 0) > 0
        elif condition == "manual_cleanup_request":
            return context.get('cleanup_requested', False)
        elif condition == "periodic_maintenance":
            return context.get('maintenance_mode', False)
        else:
            self.logger.warning(f"未知条件: {condition}")
            return False
    
    def create_agent_prompt(self, agent_name: str, trigger_type: str, context: Dict[str, Any]) -> str:
        """创建代理提示"""
        if agent_name == "function-lifecycle-manager":
            return self._create_function_lifecycle_prompt(trigger_type, context)
        else:
            return f"请使用{agent_name}代理分析以下内容:\\n{json.dumps(context, ensure_ascii=False, indent=2)}"
    
    def _create_function_lifecycle_prompt(self, trigger_type: str, context: Dict[str, Any]) -> str:
        """创建函数生命周期代理提示"""
        base_prompt = f"""我需要你使用function-lifecycle-manager代理来分析函数生命周期。

**触发类型**: {trigger_type}
**项目根目录**: {self.project_root}
**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
        
        if trigger_type == "on_function_creation":
            base_prompt += f"""**新增函数分析任务**:
1. 分析新增的 {context.get('new_functions_count', 0)} 个函数
2. 检查是否存在重复功能的函数
3. 评估函数的可重用性
4. 提供命名和设计建议
5. 建议优化和重构方案

"""
        elif trigger_type == "on_function_modification":
            base_prompt += f"""**函数修改分析任务**:
1. 分析修改的 {context.get('modified_functions_count', 0)} 个函数
2. 评估变更的影响范围
3. 检查向后兼容性
4. 分析性能影响
5. 提供重构建议

"""
        elif trigger_type == "on_code_cleanup":
            base_prompt += f"""**代码清理分析任务**:
1. 识别未使用的函数（{context.get('total_functions', 0)} 个函数中查找）
2. 建议归档方案
3. 分析删除的风险
4. 提供清理策略
5. 生成清理报告

"""
        
        # 添加分析数据文件路径
        analysis_file = context.get('analysis_file')
        if analysis_file:
            base_prompt += f"""**分析数据文件**: {analysis_file}

"""
        
        # 添加输出要求
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(self.reports_dir, f"lifecycle_analysis_{timestamp}.md")
        
        base_prompt += f"""**输出要求**:
- 使用结构化的Markdown格式
- 包含具体的代码示例和建议
- 提供可操作的改进方案
- 评估每个建议的优先级和实施难度
- 将完整报告保存到: {report_file}

请开始分析并生成详细的函数生命周期报告。"""
        
        return base_prompt
    
    def invoke_agent(self, agent_name: str, prompt: str, async_mode: bool = False) -> Tuple[bool, str, Optional[str]]:
        """调用代理"""
        self.logger.info(f"调用代理: {agent_name}")
        self.logger.debug(f"提示内容: {prompt[:200]}...")
        
        if async_mode:
            return self._invoke_agent_async(agent_name, prompt)
        else:
            return self._invoke_agent_sync(agent_name, prompt)
    
    def _invoke_agent_sync(self, agent_name: str, prompt: str) -> Tuple[bool, str, Optional[str]]:
        """同步调用代理"""
        try:
            # 创建临时文件存储提示
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(prompt)
                prompt_file = f.name
            
            # 构建Claude CLI命令
            cmd = [
                'claude',  # Claude CLI命令
                'task',    # 使用task子命令
                agent_name,  # 代理名称
                prompt     # 直接传递提示
            ]
            
            self.logger.debug(f"执行命令: {' '.join(cmd[:3])} [提示已省略]")
            
            # 执行命令
            start_time = time.time()
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.project_root
            )
            execution_time = time.time() - start_time
            
            # 清理临时文件
            try:
                os.unlink(prompt_file)
            except:
                pass
            
            success = process.returncode == 0
            output = process.stdout
            error = process.stderr if process.stderr else None
            
            self.logger.info(f"代理执行完成: 成功={success}, 耗时={execution_time:.2f}s")
            
            if not success:
                self.logger.error(f"代理执行失败: {error}")
            
            return success, output, error
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"代理执行超时 ({self.timeout}s)")
            return False, "", "执行超时"
        except FileNotFoundError:
            self.logger.error("Claude CLI 未找到，请确保已安装Claude Code")
            return False, "", "Claude CLI 未找到"
        except Exception as e:
            self.logger.error(f"代理调用异常: {e}")
            return False, "", str(e)
    
    def _invoke_agent_async(self, agent_name: str, prompt: str) -> Tuple[bool, str, Optional[str]]:
        """异步调用代理"""
        # TODO: 实现异步调用逻辑
        task_id = f"{agent_name}_{int(time.time())}"
        self.running_tasks[task_id] = {
            'agent': agent_name,
            'prompt': prompt,
            'started_at': datetime.now(),
            'status': 'running'
        }
        
        # 暂时使用同步调用
        result = self._invoke_agent_sync(agent_name, prompt)
        
        self.running_tasks[task_id]['status'] = 'completed' if result[0] else 'failed'
        self.running_tasks[task_id]['completed_at'] = datetime.now()
        
        return result
    
    def process_function_changes(self, analysis_file: str, trigger_type: str = "on_function_creation") -> bool:
        """处理函数变更"""
        self.logger.info(f"处理函数变更: {analysis_file}")
        
        # 加载分析结果
        try:
            with open(analysis_file, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
        except Exception as e:
            self.logger.error(f"无法加载分析文件: {e}")
            return False
        
        # 创建上下文
        context = {
            'analysis_file': analysis_file,
            'new_functions_count': 0,
            'modified_functions_count': 0,
            'deleted_functions_count': 0,
            'total_functions': analysis_data.get('summary', {}).get('total_functions', 0)
        }
        
        # 提取变更信息
        if 'changes' in analysis_data:
            changes = analysis_data['changes']
            context['new_functions_count'] = len(changes.get('new_functions', []))
            context['modified_functions_count'] = len(changes.get('modified_functions', []))
            context['deleted_functions_count'] = len(changes.get('deleted_functions', []))
        
        # 判断触发类型
        if context['new_functions_count'] > 0:
            trigger_type = "on_function_creation"
        elif context['modified_functions_count'] > 0:
            trigger_type = "on_function_modification"
        elif context['deleted_functions_count'] > 0:
            trigger_type = "on_code_cleanup"
        
        agent_name = "function-lifecycle-manager"
        
        # 检查是否应该触发
        if not self.should_trigger_agent(agent_name, trigger_type, context):
            self.logger.info("根据配置，不需要触发代理")
            return True
        
        # 创建提示
        prompt = self.create_agent_prompt(agent_name, trigger_type, context)
        
        # 调用代理
        success, output, error = self.invoke_agent(agent_name, prompt)
        
        if success:
            self.logger.info("代理执行成功")
            if output:
                # 保存输出到报告文件
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = os.path.join(self.reports_dir, f"agent_output_{timestamp}.md")
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(output)
                self.logger.info(f"代理输出已保存到: {output_file}")
        else:
            self.logger.error("代理执行失败")
            if error:
                self.logger.error(f"错误详情: {error}")
        
        return success
    
    def cleanup_old_tasks(self, hours: int = 24):
        """清理旧任务记录"""
        current_time = datetime.now()
        to_remove = []
        
        for task_id, task_info in self.running_tasks.items():
            started_at = task_info['started_at']
            age_hours = (current_time - started_at).total_seconds() / 3600
            
            if age_hours > hours:
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.running_tasks[task_id]
        
        if to_remove:
            self.logger.info(f"清理了 {len(to_remove)} 个旧任务记录")
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态信息"""
        return {
            'running_tasks_count': len(self.running_tasks),
            'running_tasks': list(self.running_tasks.keys()),
            'max_concurrent': self.max_concurrent,
            'timeout': self.timeout,
            'config_loaded': bool(self.config),
            'project_root': self.project_root
        }


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='代理调用器')
    parser.add_argument('--config', '-c', help='配置文件路径')
    parser.add_argument('--analysis-file', '-a', help='分析结果文件路径')
    parser.add_argument('--trigger-type', '-t', default='on_function_creation', 
                        choices=['on_function_creation', 'on_function_modification', 'on_code_cleanup'],
                        help='触发类型')
    parser.add_argument('--agent', default='function-lifecycle-manager', help='代理名称')
    parser.add_argument('--prompt', '-p', help='自定义提示')
    parser.add_argument('--async', action='store_true', help='异步模式')
    parser.add_argument('--status', action='store_true', help='显示状态')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger('AgentInvoker').setLevel(logging.DEBUG)
    
    # 初始化调用器
    invoker = AgentInvoker(args.config)
    
    if args.status:
        # 显示状态
        status = invoker.get_status()
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return
    
    if args.analysis_file:
        # 处理函数变更
        success = invoker.process_function_changes(args.analysis_file, args.trigger_type)
        sys.exit(0 if success else 1)
    elif args.prompt:
        # 直接调用代理
        success, output, error = invoker.invoke_agent(args.agent, args.prompt, args.async)
        if output:
            print(output)
        if error:
            print(f"错误: {error}", file=sys.stderr)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()