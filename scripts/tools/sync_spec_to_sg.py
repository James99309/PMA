#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规格字典 CN → SG 同步脚本

将中国 NAS (pma_synology) 的规格字典、编码字段等表同步到新加坡 NAS (pma_sa)。
支持全量同步 (--full) 和增量同步 (--incremental)。

同步范围（11 张表，按依赖顺序）：
  1. test_condition_dictionary    (无 FK)
  2. test_method_dictionary       (无 FK)
  3. spec_categories              (无 FK)
  4. specification_dictionary     (→ spec_categories, test_condition/method)
  5. specification_options        (→ specification_dictionary)
  6. spec_definitions             (→ spec_categories, test_condition/method)
  7. product_subcategories        (→ product_categories)
  8. product_code_fields          (→ product_categories, product_subcategories)
  9. product_code_field_options   (→ product_code_fields, specification_options)
 10. spec_templates               (→ product_categories, product_subcategories)
 11. spec_template_items          (→ spec_templates, spec_definitions)

用法：
  python3 scripts/tools/sync_spec_to_sg.py --full       # 全量同步
  python3 scripts/tools/sync_spec_to_sg.py --incremental # 增量同步 (仅 updated_at 表)
  python3 scripts/tools/sync_spec_to_sg.py --full --dry-run  # 仅预览，不执行
  python3 scripts/tools/sync_spec_to_sg.py --full --tables spec_categories,spec_definitions  # 指定表
"""

import argparse
import csv
import io
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

SYNC_STATE_FILE = Path(__file__).parent / '.sync_spec_last_run'

# NAS 连接配置
CN_NAS = {
    'lan': {'ssh': 'ssh -p 72 -o ConnectTimeout=5 -o BatchMode=yes james.sh@100.118.231.15'},
    'wan': {
        'tunnel': 'cloudflared access tcp --hostname ssh.jamesgpone.win --url localhost:2222',
        'ssh': 'ssh -p 2222 -o ConnectTimeout=10 james.sh@localhost',
        'proxy_port': 2222,
    },
    'docker_prefix': 'sudo /usr/local/bin/docker',
    'db_container': 'pma-postgres',
    'db_name': 'pma_synology',
    'db_user': 'pma',
    'label': 'CN-NAS/pma_synology',
}

SG_NAS = {
    'lan': {'ssh': 'ssh -o ConnectTimeout=5 -o BatchMode=yes admin@100.87.155.40'},
    'wan': {
        'tunnel': 'cloudflared access tcp --hostname sg-ssh.jamesgpone.win --url localhost:2223',
        'ssh': 'ssh -p 2223 -o ConnectTimeout=10 admin@localhost',
        'proxy_port': 2223,
    },
    'docker_prefix': "sudo sh -c 'export PATH=/usr/local/bin:$PATH && docker",
    'docker_suffix': "'",
    'db_container': 'pma-postgres',
    'db_name': 'pma_sa',
    'db_user': 'pma',
    'label': 'SG-NAS/pma_sa',
}

# 表定义：按依赖顺序排列
# columns: 所有列（按数据库顺序）
# update_cols: UPSERT 时需要更新的列（排除 id 和 created_at）
# has_updated_at: 是否有 updated_at 列（用于增量同步）
TABLES = [
    {
        'name': 'test_condition_dictionary',
        'columns': ['id', 'name', 'description', 'display_order', 'is_active', 'created_at'],
        'update_cols': ['name', 'description', 'display_order', 'is_active'],
        'has_updated_at': False,
    },
    {
        'name': 'test_method_dictionary',
        'columns': ['id', 'name', 'description', 'category', 'display_order', 'is_active', 'created_at'],
        'update_cols': ['name', 'description', 'category', 'display_order', 'is_active'],
        'has_updated_at': False,
    },
    {
        'name': 'spec_categories',
        'columns': ['id', 'code', 'name', 'name_en', 'description', 'display_order', 'is_active', 'created_at', 'updated_at'],
        'update_cols': ['code', 'name', 'name_en', 'description', 'display_order', 'is_active', 'updated_at'],
        'has_updated_at': True,
    },
    {
        'name': 'specification_dictionary',
        'columns': ['id', 'name', 'name_en', 'unit', 'category_id', 'description',
                     'value_type', 'allow_attachment', 'default_test_condition_id',
                     'default_test_method_id', 'is_active', 'display_order',
                     'created_at', 'updated_at'],
        'update_cols': ['name', 'name_en', 'unit', 'category_id', 'description',
                        'value_type', 'allow_attachment', 'default_test_condition_id',
                        'default_test_method_id', 'is_active', 'display_order', 'updated_at'],
        'has_updated_at': True,
    },
    {
        'name': 'specification_options',
        'columns': ['id', 'spec_id', 'value', 'code', 'description', 'is_active', 'position', 'created_at'],
        'update_cols': ['spec_id', 'value', 'code', 'description', 'is_active', 'position'],
        'has_updated_at': False,
    },
    {
        'name': 'spec_definitions',
        'columns': ['id', 'category_id', 'name', 'name_en', 'unit', 'description', 'value_type',
                     'allow_attachment', 'default_test_condition_id', 'default_test_method_id',
                     'display_order', 'is_active', 'created_at', 'updated_at'],
        'update_cols': ['category_id', 'name', 'name_en', 'unit', 'description', 'value_type',
                        'allow_attachment', 'default_test_condition_id', 'default_test_method_id',
                        'display_order', 'is_active', 'updated_at'],
        'has_updated_at': True,
    },
    {
        'name': 'product_subcategories',
        'columns': ['id', 'category_id', 'name', 'code_letter', 'description', 'display_order',
                     'created_at', 'updated_at', 'image_path', 'pdf_path', 'name_en'],
        'update_cols': ['category_id', 'name', 'code_letter', 'description', 'display_order',
                        'updated_at', 'image_path', 'pdf_path', 'name_en'],
        'has_updated_at': True,
    },
    {
        'name': 'product_code_fields',
        'columns': ['id', 'subcategory_id', 'name', 'code', 'description', 'field_type', 'position',
                     'max_length', 'is_required', 'use_in_code', 'created_at', 'updated_at',
                     'category_id', 'allow_quotation_config', 'name_en'],
        'update_cols': ['subcategory_id', 'name', 'code', 'description', 'field_type', 'position',
                        'max_length', 'is_required', 'use_in_code', 'updated_at',
                        'category_id', 'allow_quotation_config', 'name_en'],
        'has_updated_at': True,
    },
    {
        'name': 'product_code_field_options',
        'columns': ['id', 'field_id', 'value', 'code', 'description', 'is_active', 'position',
                     'created_at', 'updated_at', 'spec_option_id', 'price_adjustment',
                     'subcategory_id', 'allow_quotation_config'],
        'update_cols': ['field_id', 'value', 'code', 'description', 'is_active', 'position',
                        'updated_at', 'spec_option_id', 'price_adjustment',
                        'subcategory_id', 'allow_quotation_config'],
        'has_updated_at': True,
    },
    {
        'name': 'spec_templates',
        'columns': ['id', 'model', 'name', 'name_en', 'description', 'version',
                     'version_first_used_at', 'is_active', 'created_by', 'created_at',
                     'updated_at', 'category_id', 'subcategory_id'],
        'update_cols': ['model', 'name', 'name_en', 'description', 'version',
                        'version_first_used_at', 'is_active', 'created_by',
                        'updated_at', 'category_id', 'subcategory_id'],
        'has_updated_at': True,
    },
    {
        'name': 'spec_template_items',
        'columns': ['id', 'template_id', 'definition_id', 'general_value',
                     'test_condition_id', 'test_condition_text', 'test_method_id',
                     'test_method_text', 'display_order', 'is_required', 'options',
                     'created_at', 'updated_at', 'use_in_code', 'code_length',
                     'spec_dict_id'],
        'update_cols': ['template_id', 'definition_id', 'general_value',
                        'test_condition_id', 'test_condition_text', 'test_method_id',
                        'test_method_text', 'display_order', 'is_required', 'options',
                        'updated_at', 'use_in_code', 'code_length', 'spec_dict_id'],
        'has_updated_at': True,
    },
]


# ---------------------------------------------------------------------------
# SSH 连接
# ---------------------------------------------------------------------------

class NASConnection:
    """管理到 NAS 的 SSH 连接"""

    def __init__(self, config: dict):
        self.config = config
        self.ssh_cmd = None  # 将被设置为实际可用的 ssh 命令
        self.label = config['label']

    def connect(self) -> bool:
        """自动检测内网/外网并建立连接"""
        # 尝试内网
        lan_ssh = self.config['lan']['ssh']
        result = subprocess.run(
            f'{lan_ssh} "echo ok"',
            shell=True, capture_output=True, text=True, timeout=8
        )
        if result.returncode == 0 and 'ok' in result.stdout:
            self.ssh_cmd = lan_ssh.replace(' -o ConnectTimeout=5', '').replace(' -o BatchMode=yes', '')
            print(f"  [{self.label}] 内网连接成功")
            return True

        # 尝试外网
        print(f"  [{self.label}] 内网不可达，尝试外网...")
        wan = self.config['wan']

        # 检查代理是否已运行
        check = subprocess.run(
            f'pgrep -f "cloudflared.*localhost:{wan["proxy_port"]}"',
            shell=True, capture_output=True, text=True
        )
        if check.returncode != 0:
            # 启动代理
            subprocess.Popen(
                wan['tunnel'], shell=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            time.sleep(3)

        # 测试外网
        wan_ssh = wan['ssh']
        result = subprocess.run(
            f'{wan_ssh} "echo ok"',
            shell=True, capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and 'ok' in result.stdout:
            self.ssh_cmd = wan_ssh.replace(' -o ConnectTimeout=10', '')
            print(f"  [{self.label}] 外网连接成功")
            return True

        print(f"  [{self.label}] 连接失败！")
        return False

    def _build_psql_cmd(self, sql: str, copy_mode=False) -> str:
        """构建通过 SSH 执行 psql 的命令"""
        cfg = self.config
        container = cfg['db_container']
        db = cfg['db_name']
        user = cfg['db_user']

        if 'docker_suffix' in cfg:
            # SG NAS 格式
            prefix = cfg['docker_prefix']
            suffix = cfg['docker_suffix']
            if copy_mode:
                return f'{self.ssh_cmd} "{prefix} exec -i {container} psql -U {user} {db}{suffix}"'
            else:
                # 对 SQL 中的单引号进行转义
                escaped_sql = sql.replace("'", "'\\''")
                return f'{self.ssh_cmd} "{prefix} exec -i {container} psql -U {user} {db} -c \\"{escaped_sql}\\"{suffix}"'
        else:
            # CN NAS 格式
            docker = cfg['docker_prefix']
            if copy_mode:
                return f'{self.ssh_cmd} "{docker} exec -i {container} psql -U {user} {db}"'
            else:
                escaped_sql = sql.replace("'", "'\\''")
                return f"""{self.ssh_cmd} "{docker} exec -i {container} psql -U {user} {db} -c '{escaped_sql}'" """

    def execute_sql(self, sql: str, timeout=30) -> str:
        """执行 SQL 并返回结果"""
        cmd = self._build_psql_cmd(sql)
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0 and result.stderr.strip():
            # Filter out SSH tunnel noise
            err = '\n'.join(l for l in result.stderr.strip().split('\n')
                           if 'INF' not in l and 'ERR' not in l)
            if err.strip():
                raise RuntimeError(f"[{self.label}] SQL error: {err}")
        return result.stdout

    def copy_to_csv(self, table: str, columns: list, where: str = '') -> str:
        """使用 COPY TO STDOUT 导出 CSV 数据"""
        cols = ', '.join(columns)
        if where:
            copy_sql = f"COPY (SELECT {cols} FROM {table} WHERE {where}) TO STDOUT WITH (FORMAT csv, HEADER true, NULL '\\N')"
        else:
            copy_sql = f"COPY (SELECT {cols} FROM {table}) TO STDOUT WITH (FORMAT csv, HEADER true, NULL '\\N')"

        cmd = self._build_psql_cmd(copy_sql, copy_mode=True)
        # For COPY, we pipe the SQL through stdin
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=60,
            input=copy_sql
        )
        if result.returncode != 0:
            err = '\n'.join(l for l in result.stderr.strip().split('\n')
                           if 'INF' not in l and 'ERR' not in l)
            if err.strip():
                raise RuntimeError(f"[{self.label}] COPY error: {err}")
        return result.stdout

    def pipe_sql(self, sql_text: str, timeout=120) -> str:
        """通过管道将大量 SQL 发送到 psql"""
        cmd = self._build_psql_cmd('', copy_mode=True)
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout,
            input=sql_text
        )
        if result.returncode != 0:
            err = '\n'.join(l for l in result.stderr.strip().split('\n')
                           if 'INF' not in l and 'ERR' not in l)
            if err.strip():
                raise RuntimeError(f"[{self.label}] Pipe SQL error: {err}")
        return result.stdout

    def get_count(self, table: str) -> int:
        """获取表行数"""
        out = self.execute_sql(f"SELECT COUNT(*) FROM {table};")
        for line in out.strip().split('\n'):
            line = line.strip()
            if line.isdigit():
                return int(line)
        return -1


# ---------------------------------------------------------------------------
# CSV → UPSERT 转换
# ---------------------------------------------------------------------------

def csv_to_upsert_sql(csv_data: str, table_def: dict) -> str:
    """将 CSV 数据转换为 UPSERT SQL 语句"""
    reader = csv.DictReader(io.StringIO(csv_data))
    columns = table_def['columns']
    update_cols = table_def['update_cols']
    table = table_def['name']

    rows = list(reader)
    if not rows:
        return ''

    lines = ['BEGIN;']

    for row in rows:
        values = []
        for col in columns:
            val = row.get(col, '')
            if val == '\\N' or val == '' and col != 'description':
                values.append('NULL')
            elif col == 'options':
                # JSON 列 - 需要特殊处理
                if val and val != '\\N':
                    escaped = val.replace("'", "''")
                    values.append(f"'{escaped}'::jsonb")
                else:
                    values.append('NULL')
            elif val in ('true', 'false', 't', 'f'):
                values.append('true' if val in ('true', 't') else 'false')
            elif _is_numeric(val):
                values.append(val)
            else:
                escaped = val.replace("'", "''")
                values.append(f"'{escaped}'")

        cols_str = ', '.join(columns)
        vals_str = ', '.join(values)
        update_str = ', '.join(f'{c}=EXCLUDED.{c}' for c in update_cols)

        lines.append(
            f"INSERT INTO {table} ({cols_str}) VALUES ({vals_str}) "
            f"ON CONFLICT (id) DO UPDATE SET {update_str};"
        )

    lines.append('COMMIT;')
    return '\n'.join(lines)


def _is_numeric(s: str) -> bool:
    """检查字符串是否为数值"""
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# 同步逻辑
# ---------------------------------------------------------------------------

def load_last_sync_time() -> str | None:
    """加载上次同步时间"""
    if SYNC_STATE_FILE.exists():
        data = json.loads(SYNC_STATE_FILE.read_text())
        return data.get('last_sync_at')
    return None


def save_sync_time(ts: str):
    """保存同步时间"""
    SYNC_STATE_FILE.write_text(json.dumps({
        'last_sync_at': ts,
        'updated': datetime.now(timezone.utc).isoformat(),
    }, indent=2))


def sync_table(cn: NASConnection, sg: NASConnection, table_def: dict,
               incremental: bool = False, last_sync_at: str | None = None,
               dry_run: bool = False) -> dict:
    """同步单张表，返回统计信息"""
    table = table_def['name']
    columns = table_def['columns']
    has_updated_at = table_def['has_updated_at']

    result = {'table': table, 'status': 'skipped', 'cn_count': 0, 'sg_before': 0, 'sg_after': 0}

    # 增量模式下，无 updated_at 的表跳过
    if incremental and not has_updated_at:
        print(f"  [{table}] 跳过 (无 updated_at 列)")
        return result

    # 构建 WHERE 子句
    where = ''
    if incremental and has_updated_at and last_sync_at:
        where = f"updated_at > '{last_sync_at}'"
        print(f"  [{table}] 增量同步: {where}")

    # 获取 SG 当前行数
    result['sg_before'] = sg.get_count(table)

    # 从 CN 导出 CSV
    print(f"  [{table}] 导出 CN 数据...", end='', flush=True)
    csv_data = cn.copy_to_csv(table, columns, where)
    row_count = csv_data.strip().count('\n')  # 减去 header
    print(f" {row_count} 行")
    result['cn_count'] = row_count

    if row_count == 0:
        result['status'] = 'no_data'
        return result

    # 转换为 UPSERT SQL
    upsert_sql = csv_to_upsert_sql(csv_data, table_def)

    if dry_run:
        # 预览模式 - 显示前几条
        lines = upsert_sql.split('\n')
        preview_lines = [l for l in lines if l.startswith('INSERT')][:3]
        for l in preview_lines:
            print(f"    预览: {l[:120]}...")
        result['status'] = 'dry_run'
        return result

    # 执行 UPSERT
    print(f"  [{table}] UPSERT 到 SG...", end='', flush=True)
    output = sg.pipe_sql(upsert_sql, timeout=120)
    insert_count = output.count('INSERT')
    print(f" {insert_count} 条完成")

    # 验证结果
    result['sg_after'] = sg.get_count(table)
    result['status'] = 'ok' if result['sg_after'] >= result['cn_count'] else 'partial'

    return result


def reset_sequences(sg: NASConnection, tables: list[dict]):
    """重置所有表的序列"""
    print("\n重置序列...")
    for tdef in tables:
        table = tdef['name']
        sql = (f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
               f"COALESCE((SELECT MAX(id) FROM {table}), 1));")
        try:
            out = sg.execute_sql(sql)
            for line in out.strip().split('\n'):
                line = line.strip()
                if line.isdigit():
                    print(f"  {table}: 序列 → {line}")
        except Exception as e:
            print(f"  {table}: 序列重置失败 - {e}")


def verify_fk_integrity(sg: NASConnection):
    """验证 FK 完整性"""
    print("\n验证 FK 完整性...")
    checks = [
        ("specification_options → specification_dictionary",
         "SELECT COUNT(*) FROM specification_options so "
         "WHERE NOT EXISTS (SELECT 1 FROM specification_dictionary sd WHERE sd.id = so.spec_id)"),
        ("spec_definitions → spec_categories",
         "SELECT COUNT(*) FROM spec_definitions sd "
         "WHERE sd.category_id IS NOT NULL AND "
         "NOT EXISTS (SELECT 1 FROM spec_categories sc WHERE sc.id = sd.category_id)"),
        ("product_code_field_options → product_code_fields",
         "SELECT COUNT(*) FROM product_code_field_options pco "
         "WHERE pco.field_id IS NOT NULL AND "
         "NOT EXISTS (SELECT 1 FROM product_code_fields pcf WHERE pcf.id = pco.field_id)"),
        ("product_code_field_options → specification_options",
         "SELECT COUNT(*) FROM product_code_field_options pco "
         "WHERE pco.spec_option_id IS NOT NULL AND "
         "NOT EXISTS (SELECT 1 FROM specification_options so WHERE so.id = pco.spec_option_id)"),
        ("spec_template_items → spec_templates",
         "SELECT COUNT(*) FROM spec_template_items sti "
         "WHERE NOT EXISTS (SELECT 1 FROM spec_templates st WHERE st.id = sti.template_id)"),
        ("spec_template_items → spec_definitions",
         "SELECT COUNT(*) FROM spec_template_items sti "
         "WHERE sti.definition_id IS NOT NULL AND "
         "NOT EXISTS (SELECT 1 FROM spec_definitions sd WHERE sd.id = sti.definition_id)"),
        ("spec_template_items → specification_dictionary",
         "SELECT COUNT(*) FROM spec_template_items sti "
         "WHERE sti.spec_dict_id IS NOT NULL AND "
         "NOT EXISTS (SELECT 1 FROM specification_dictionary sd WHERE sd.id = sti.spec_dict_id)"),
    ]

    all_ok = True
    for label, sql in checks:
        try:
            out = sg.execute_sql(f"{sql};")
            count = 0
            for line in out.strip().split('\n'):
                line = line.strip()
                if line.isdigit():
                    count = int(line)
            status = "✅" if count == 0 else f"❌ {count} 孤儿"
            print(f"  {label}: {status}")
            if count > 0:
                all_ok = False
        except Exception as e:
            print(f"  {label}: ⚠️ 检查失败 - {e}")
            all_ok = False

    return all_ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='CN → SG 规格字典同步')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--full', action='store_true', help='全量同步')
    mode.add_argument('--incremental', action='store_true', help='增量同步 (仅 updated_at 表)')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不执行写入')
    parser.add_argument('--tables', type=str, default='',
                        help='指定同步的表（逗号分隔），默认全部')
    parser.add_argument('--skip-verify', action='store_true', help='跳过 FK 验证')
    parser.add_argument('--skip-sequences', action='store_true', help='跳过序列重置')

    args = parser.parse_args()

    mode_label = '全量同步' if args.full else '增量同步'
    print(f"╔══════════════════════════════════════════╗")
    print(f"║  CN → SG 规格字典同步  [{mode_label}]  ║")
    print(f"╚══════════════════════════════════════════╝")
    if args.dry_run:
        print("⚠️  预览模式 - 不会执行任何写入操作")
    print()

    # 筛选表
    if args.tables:
        selected = set(args.tables.split(','))
        tables = [t for t in TABLES if t['name'] in selected]
        unknown = selected - {t['name'] for t in tables}
        if unknown:
            print(f"⚠️  未知的表: {', '.join(unknown)}")
            print(f"   可选: {', '.join(t['name'] for t in TABLES)}")
            sys.exit(1)
    else:
        tables = TABLES

    # 建立连接
    print("建立连接...")
    cn = NASConnection(CN_NAS)
    sg = NASConnection(SG_NAS)

    if not cn.connect():
        print("❌ 无法连接中国 NAS")
        sys.exit(1)
    if not sg.connect():
        print("❌ 无法连接新加坡 NAS")
        sys.exit(1)
    print()

    # 增量模式加载上次同步时间
    last_sync_at = None
    if args.incremental:
        last_sync_at = load_last_sync_time()
        if last_sync_at:
            print(f"上次同步: {last_sync_at}")
        else:
            print("⚠️  未找到上次同步记录，将执行全量同步")
            args.full = True
        print()

    # 记录开始时间
    sync_start = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

    # 同步每张表
    results = []
    print(f"同步 {len(tables)} 张表...")
    print("-" * 60)
    for tdef in tables:
        try:
            r = sync_table(cn, sg, tdef,
                           incremental=args.incremental,
                           last_sync_at=last_sync_at,
                           dry_run=args.dry_run)
            results.append(r)
        except Exception as e:
            print(f"  [{tdef['name']}] ❌ 错误: {e}")
            results.append({
                'table': tdef['name'], 'status': 'error',
                'cn_count': 0, 'sg_before': 0, 'sg_after': 0, 'error': str(e)
            })

    # 重置序列
    if not args.dry_run and not args.skip_sequences:
        reset_sequences(sg, tables)

    # FK 验证
    fk_ok = True
    if not args.dry_run and not args.skip_verify:
        fk_ok = verify_fk_integrity(sg)

    # 保存同步时间
    if not args.dry_run:
        save_sync_time(sync_start)

    # 输出汇总
    print()
    print("=" * 60)
    print("同步结果汇总")
    print("=" * 60)
    print(f"{'表名':<35} {'CN':>5} {'SG前':>5} {'SG后':>5} {'状态':>8}")
    print("-" * 60)
    for r in results:
        status_icon = {
            'ok': '✅', 'dry_run': '👁️', 'skipped': '⏭️',
            'no_data': '📭', 'partial': '⚠️', 'error': '❌'
        }.get(r['status'], '?')
        print(f"  {r['table']:<33} {r['cn_count']:>5} {r['sg_before']:>5} {r['sg_after']:>5} {status_icon:>6}")

    if not args.dry_run:
        print(f"\n同步时间已记录: {sync_start}")

    # 检查是否有错误
    errors = [r for r in results if r['status'] == 'error']
    if errors:
        print(f"\n❌ {len(errors)} 张表同步失败")
        sys.exit(1)
    elif not fk_ok:
        print("\n⚠️  FK 完整性检查发现问题")
        sys.exit(1)
    else:
        print("\n✅ 同步完成")


if __name__ == '__main__':
    main()
