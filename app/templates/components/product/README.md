# 产品模块专用组件

此目录包含**仅用于产品库和研发库**的 Tailwind 组件。

## 组件列表

| 组件文件 | 功能描述 | 使用页面 |
|---------|---------|---------|
| `tw_product_modal.html` | 产品创建/编辑模态框 | 产品库列表、研发库列表、详情页 |
| `tw_product_relation_modal.html` | 产品关联配置模态框 | 产品库详情页 |
| `tw_spec_list.html` | 规格列表显示组件 | 产品库详情页、研发库详情页 |
| `tw_spec_modals.html` | 规格预览/冲突模态框 | 产品库详情页、研发库详情页 |
| `tw_spec_options_modal.html` | 规格选项管理模态框 | 产品库详情页、研发库详情页 |

## 使用方式

```jinja2
{% from 'components/product/tw_product_modal.html' import render_product_modal, render_product_modal_script %}
{% from 'components/product/tw_spec_list.html' import render_tw_spec_list %}
{% from 'components/product/tw_spec_modals.html' import tw_spec_preview_modal, tw_spec_conflict_modal %}
{% from 'components/product/tw_spec_options_modal.html' import tw_spec_options_modal, tw_spec_options_modal_script %}
{% from 'components/product/tw_product_relation_modal.html' import render_tw_product_relation_modal, render_tw_product_relation_script %}
```

## 与通用组件的区别

- **此目录组件**: 仅服务于产品库 (`product/`) 和研发库 (`product_management/`)
- **通用组件** (`components/`): 可被多个模块使用（如 `tw_product_spec_modal.html` 用于报价单、项目等）

## 相关 JavaScript

- `app/static/js/spec-editor.js` - 规格编辑器核心逻辑（产品库/研发库共用）
