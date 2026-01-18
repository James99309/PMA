"""
=============================================================================
SP8D系统API客户端服务
=============================================================================

用于OVS系统调用SP8D系统API的客户端封装。
支持配置树、产品配置等API的调用。

版本：1.0
最后更新：2025-01-15
"""

import requests
import os
import logging

logger = logging.getLogger(__name__)


class SP8DAPIService:
    """SP8D系统API客户端

    用于OVS系统跨系统调用SP8D的API端点。
    包含简单的错误处理和日志记录。

    Attributes:
        base_url (str): SP8D API基础URL
        api_key (str): 跨系统调用的API Key
        session (requests.Session): 复用的HTTP会话
    """

    def __init__(self):
        """初始化SP8D API客户端

        从环境变量读取配置：
        - SP8D_API_BASE_URL: SP8D API基础URL（例如：https://sp8d.yourdomain.com/api/v1）
        - SP8D_API_KEY: 跨系统调用的API Key
        """
        self.base_url = os.environ.get('SP8D_API_BASE_URL')
        self.api_key = os.environ.get('SP8D_API_KEY')

        # 初始化会话
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'OVS/1.0'
        })

        # 验证配置
        if not self.base_url or not self.api_key:
            logger.warning("SP8D API配置不完整")

    def get_configurations_tree(self):
        """获取SP8D配置树数据

        调用SP8D的 /configurations-tree API端点，获取可引入的配置产品树。

        Returns:
            list: 配置树数据（格式同SP8D本地API）
                失败返回 None，错误信息写入日志

        Raises:
            无异常抛出，所有错误都返回 None 并记录日志
        """
        try:
            if not self.base_url or not self.api_key:
                logger.error("SP8D API配置不完整，无法发起请求")
                return None

            # 发起GET请求
            response = self.session.get(
                f'{self.base_url}/configurations-tree',
                timeout=10
            )
            response.raise_for_status()

            # 解析JSON响应
            data = response.json()

            # 检查API响应状态
            if data.get('success'):
                tree_data = data.get('data', [])
                logger.info(f"成功获取SP8D配置树，包含 {len(tree_data)} 个分类")
                return tree_data
            else:
                error_msg = data.get('message', '未知错误')
                logger.error(f"获取SP8D配置树失败: {error_msg}")
                return None

        except requests.exceptions.Timeout:
            logger.error("SP8D API请求超时（10秒）")
            return None

        except requests.exceptions.ConnectionError as e:
            logger.error(f"SP8D API连接失败: {e}")
            return None

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 'unknown'
            logger.error(f"SP8D API返回错误状态码: {status_code}")
            return None

        except ValueError as e:
            logger.error(f"SP8D API响应解析失败（无效JSON）: {e}")
            return None

        except Exception as e:
            logger.error(f"调用SP8D API失败: {type(e).__name__}: {e}")
            return None

    def get_configuration_specs(self, config_id):
        """获取SP8D配置版本的规格数据

        调用SP8D的 /configurations/{config_id}/specs API端点，获取配置的规格数据。
        用于OVS从SP8D导入产品时自动导入规格。

        Args:
            config_id: SP8D配置版本ID

        Returns:
            dict: 规格数据 {"configuration": {...}, "specs": [...]}
                失败返回 None，错误信息写入日志

        Raises:
            无异常抛出，所有错误都返回 None 并记录日志
        """
        try:
            if not self.base_url or not self.api_key:
                logger.error("SP8D API配置不完整，无法发起请求")
                return None

            # 发起GET请求
            response = self.session.get(
                f'{self.base_url}/configurations/{config_id}/specs',
                timeout=10
            )
            response.raise_for_status()

            # 解析JSON响应
            data = response.json()

            # 检查API响应状态
            if data.get('success'):
                spec_data = data.get('data')
                specs_count = len(spec_data.get('specs', [])) if spec_data else 0
                logger.info(f"成功获取SP8D配置 {config_id} 的规格数据，共 {specs_count} 条")
                return spec_data
            else:
                error_msg = data.get('message', '未知错误')
                logger.error(f"获取SP8D配置规格失败: {error_msg}")
                return None

        except requests.exceptions.Timeout:
            logger.error("SP8D API请求超时（10秒）")
            return None

        except requests.exceptions.ConnectionError as e:
            logger.error(f"SP8D API连接失败: {e}")
            return None

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 'unknown'
            logger.error(f"SP8D API返回错误状态码: {status_code}")
            return None

        except ValueError as e:
            logger.error(f"SP8D API响应解析失败（无效JSON）: {e}")
            return None

        except Exception as e:
            logger.error(f"调用SP8D规格API失败: {type(e).__name__}: {e}")
            return None


# 全局实例 - 模块加载时创建
sp8d_api_service = SP8DAPIService()
