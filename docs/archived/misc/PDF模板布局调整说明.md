# PDF模板布局调整说明

## 调整概述

根据提供的参考PDF图片"提货批价单-上海名人苑-2025-04-22_12.12.pdf"，我们对批价单、结算单和合并PDF的模板进行了重大布局调整，使其更符合和源通信的标准格式。

## 主要调整内容

### 1. 页面头部布局重构

**调整前：**
- 公司名称、文档标题、签名都居中显示
- 缺少公司详细地址信息
- 布局较为简单

**调整后：**
- **左侧区域**：公司信息
  - 和源通信（上海）股份有限公司
  - 完整地址：武威路88弄19号楼6楼、普陀区 上海市、中国 (200335)
  - 联系方式：021-62596028、www.evertac.net
- **右侧区域**：文档标题和签名
  - 文档标题（批价单/结算单/批价结算单）
  - signature标识

### 2. 样式优化

**字体和尺寸调整：**
- 公司名称：18px → 16px
- 公司地址：新增，10px，行高1.3
- 文档标题：保持24px，去除字间距
- 签名：10px → 12px，添加灰色

**布局改进：**
- 使用Flexbox布局实现左右分栏
- 左侧公司信息左对齐
- 右侧文档信息右对齐
- 去除原有的居中对齐和底部边框

### 3. 金额汇总区域优化

**调整前：**
- 简单的居中显示
- 所有金额信息在一行

**调整后：**
- 添加背景色和边框
- 使用Flexbox布局分离左右内容
- 左侧：总金额标签和原始金额
- 右侧：折扣后金额
- 增强视觉层次感

### 4. 产品分类汇总改进

**样式优化：**
- 添加边框包围整个汇总区域
- 调整行间距和内边距
- 优化最后一行的边框显示
- 字体大小从11px调整为10px

### 5. 三个模板的一致性

所有调整同时应用到：
- `pricing_order_template.html` (批价单)
- `settlement_order_template.html` (结算单)  
- `combined_order_template.html` (合并PDF)

确保三个模板保持一致的视觉风格和布局结构。

## 技术实现细节

### CSS关键变更

```css
/* 新的页面头部样式 */
.page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 20px;
    padding-bottom: 15px;
}

.company-info {
    flex: 1;
    text-align: left;
}

.document-header {
    flex: 1;
    text-align: right;
}
```

### HTML结构调整

```html
<div class="page-header">
    <div class="company-info">
        <div class="company-name">和源通信（上海）股份有限公司</div>
        <div class="company-address">
            <div>武威路88弄19号楼6楼</div>
            <div>普陀区 上海市</div>
            <div>中国 (200335)</div>
            <div>021-62596028</div>
            <div>www.evertac.net</div>
        </div>
    </div>
    <div class="document-header">
        <div class="document-title">批价单</div>
        <div class="signature">signature: {{ pricing_order.order_number }}</div>
    </div>
</div>
```

## 测试结果

更新后的PDF文件大小：
- 批价单PDF: 61,007 bytes
- 结算单PDF: 60,674 bytes  
- 合并PDF: 61,547 bytes

## 视觉效果对比

**参考图片特点：**
- 专业的商务文档风格
- 清晰的信息层次
- 左右分栏的平衡布局
- 完整的公司信息展示

**调整后效果：**
- ✅ 完全符合参考图片的布局结构
- ✅ 保持了和源通信的品牌形象
- ✅ 提升了文档的专业性和可读性
- ✅ 三种PDF模板风格统一

## 总结

通过这次布局调整，我们成功地将PDF模板从简单的居中布局升级为专业的商务文档格式，完全符合参考图片的设计标准。新的布局不仅视觉效果更佳，也更好地体现了和源通信的企业形象和专业水准。 