# Windows PDF乱码问题修复方案

## 问题分析

### 根本原因
Windows浏览器导出批价单PDF出现乱码的原因：

1. **字体不匹配**：HTML模板中使用的字体与Windows系统实际可用字体不匹配
2. **字体加载失败**：WeasyPrint在Windows环境下无法正确加载中文字体
3. **字符编码问题**：PDF生成时字符编码处理不当

### 当前字体配置问题

**HTML模板字体设置**（有问题）：
```css
font-family: "Songti SC", "宋体", "SimSun", "Arial", sans-serif;
```

**PDF生成器字体设置**（部分正确）：
```python
# Windows平台
font_family = '"Microsoft YaHei", "微软雅黑", "DengXian", "等线", "SimSun", "宋体", "Arial", sans-serif'
```

**问题**：
- HTML模板优先使用macOS字体 "Songti SC"
- Windows系统没有 "Songti SC" 字体
- 字体回退机制不完善

## 修复方案

### 方案1：统一字体配置（推荐）

修改HTML模板，使其根据服务器操作系统动态选择字体。

### 方案2：增强字体检测

改进PDF生成器的字体检测和配置逻辑。

### 方案3：添加字体文件

在项目中添加通用中文字体文件。

## 具体实施

### 1. 修复HTML模板字体配置

需要修改以下文件：
- `app/templates/pdf/pricing_order_template.html`
- `app/templates/pdf/settlement_order_template.html`
- `app/templates/pdf/quotation_template.html`
- `app/templates/pdf/order_template.html`

### 2. 改进PDF生成器

增强 `app/services/pdf_generator.py` 中的字体处理逻辑。

### 3. 添加字体检测功能

创建字体可用性检测机制。

## 技术细节

### Windows常见中文字体路径
```
C:/Windows/Fonts/msyh.ttc      # 微软雅黑 (推荐)
C:/Windows/Fonts/msyhbd.ttc    # 微软雅黑 Bold
C:/Windows/Fonts/simsun.ttc    # 宋体
C:/Windows/Fonts/simhei.ttf    # 黑体
C:/Windows/Fonts/DengXian.ttf  # 等线 (Windows 10+)
```

### 字体优先级建议
1. **微软雅黑** - 现代、清晰、支持完整
2. **等线** - Windows 10默认中文字体
3. **宋体** - 传统中文字体，兼容性好
4. **Arial** - 英文字体回退

## 立即修复步骤

### 步骤1：检查服务器字体
```bash
# 检查Windows服务器字体
dir C:\Windows\Fonts\*yh*.ttc    # 微软雅黑
dir C:\Windows\Fonts\*sim*.ttc   # 宋体
dir C:\Windows\Fonts\*Deng*.ttf  # 等线
```

### 步骤2：修改字体配置
将在下一步提供具体的代码修改。

### 步骤3：测试验证
使用童蕾账户测试PDF导出功能。

## 预期效果

修复后应该实现：
- ✅ Windows浏览器正常显示中文字符
- ✅ PDF文件在不同设备上显示一致
- ✅ 保持原有的排版和样式
- ✅ 提高字体加载速度

## 兼容性考虑

- **Windows 7/8/10/11**：全面支持
- **不同浏览器**：Chrome、Firefox、Edge、IE11+
- **服务器环境**：Windows Server 2012+
- **字体许可**：使用系统自带字体，无版权问题

## 后续优化

1. **字体缓存**：缓存字体检测结果
2. **字体预加载**：提前加载常用字体
3. **字体压缩**：优化字体文件大小
4. **多语言支持**：支持其他语言字体 