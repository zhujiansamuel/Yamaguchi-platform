# 📝 買取申込書模板编辑器使用指南

## 🌟 功能介绍

这是一个基于 GrapesJS 的可视化模板编辑器，专门用于编辑买取申込書（买取申请书）模板。

### 主要功能

- ✅ **可视化拖拽编辑**：使用 GrapesJS 提供的组件进行拖拽式编辑
- ✅ **实时预览**：在编辑器中实时查看修改效果
- ✅ **自动备份**：每次保存时自动创建备份文件
- ✅ **响应式设计**：支持桌面、平板、手机三种设备视图
- ✅ **代码导出**：可以导出完整的 HTML 代码

## 🚀 访问编辑器

### 访问地址

```
http://localhost:8080/index/index/template_editor
```

### 快捷访问

在浏览器中打开开发服务器后，直接访问上述地址即可进入编辑器。

## 🎨 编辑器界面说明

### 顶部工具栏

- **🔄 重新加载**：重新从服务器加载模板内容
- **👁️ 预览**：在新窗口中预览当前编辑的内容
- **💾 保存模板**：保存修改后的模板到服务器
- **📤 导出代码**：下载完整的 HTML 代码到本地

### 左侧面板

- **Blocks（组件）**：可拖拽的预设组件
  - 文本块
  - 图片
  - 表格
  - 按钮
  - 链接
  - 容器
  - 等等...

### 右侧面板

- **Style Manager（样式管理器）**：修改选中元素的 CSS 样式
- **Trait Manager（属性管理器）**：修改选中元素的 HTML 属性

### 中央画布

- **编辑区域**：主要的编辑工作区
- **设备切换**：顶部可切换桌面/平板/手机视图

## 📋 使用步骤

### 1. 打开编辑器

访问 `http://localhost:8080/index/index/template_editor`

### 2. 自动加载模板

页面加载完成后，会自动从服务器加载当前的 ylindex.html 模板内容。

### 3. 编辑模板

#### 方式一：直接修改现有元素

1. 在画布中点击要修改的元素
2. 在右侧的 Style Manager 中修改样式
3. 在右侧的 Trait Manager 中修改属性

#### 方式二：拖拽新组件

1. 从左侧 Blocks 面板拖拽组件到画布
2. 调整组件位置和大小
3. 修改组件的样式和内容

#### 方式三：编辑代码

1. 点击左侧工具栏的 `</>` 代码图标
2. 直接编辑 HTML/CSS 代码
3. 保存后即可看到效果

### 4. 预览效果

点击顶部工具栏的 **👁️ 预览** 按钮，在新窗口中查看实际效果。

### 5. 保存模板

点击 **💾 保存模板** 按钮，系统会：

1. 自动创建备份文件（格式：`ylindex.html.backup.YYYYMMDDHHmmss`）
2. 保存新的模板内容
3. 显示成功消息和备份文件名

### 6. 导出代码（可选）

点击 **📤 导出代码** 按钮，下载完整的 HTML 文件到本地。

## 🔧 技术细节

### API 端点

#### 1. 获取模板内容

```
GET /index/index/get_template
```

**响应示例：**

```json
{
  "code": 1,
  "data": "<html>...</html>"
}
```

#### 2. 保存模板内容

```
POST /index/index/save_template
```

**请求参数：**

- `content`（string）：完整的模板内容

**响应示例：**

```json
{
  "code": 1,
  "msg": "保存成功",
  "backup": "ylindex.html.backup.20251126120000"
}
```

### 文件结构

```
application/index/
├── controller/
│   └── Index.php              # 控制器（包含编辑器方法）
└── view/index/
    ├── ylindex.html           # 原始模板（被编辑的文件）
    ├── ylindex.html.backup.*  # 自动备份文件
    └── template_editor.html   # 编辑器页面
```

### 备份机制

每次保存时，系统会自动创建备份文件：

- 备份文件名格式：`ylindex.html.backup.YYYYMMDDHHmmss`
- 保存位置：`application/index/view/index/`
- 备份文件可用于恢复之前的版本

### 恢复备份

如果需要恢复某个备份版本：

```bash
# 进入模板目录
cd application/index/view/index/

# 查看所有备份
ls -la ylindex.html.backup.*

# 恢复指定备份（示例）
cp ylindex.html.backup.20251126120000 ylindex.html
```

## ⚠️ 注意事项

1. **ThinkPHP 模板语法**：
   - 编辑器会保留 ThinkPHP 的模板标签（如 `{$order.no}`）
   - 保存时会自动包装在完整的模板结构中

2. **样式冲突**：
   - 编辑器使用的是内联样式和 `<style>` 标签
   - 修改样式时注意不要覆盖关键的布局样式

3. **定期备份**：
   - 虽然系统会自动备份，建议定期手动备份重要版本
   - 可以将备份文件复制到其他位置保存

4. **浏览器兼容性**：
   - 推荐使用 Chrome、Edge、Firefox 等现代浏览器
   - 不支持 IE 浏览器

## 🎯 常见修改场景

### 修改客户信息表格

1. 在画布中找到客户信息表格
2. 点击要修改的单元格
3. 双击直接编辑文字或在右侧修改样式

### 修改背景颜色

1. 选中要修改的元素（如表头）
2. 在右侧 Style Manager 中找到 "Background"
3. 修改 background-color 属性

### 添加新字段

1. 从左侧拖拽 "Table Row" 组件到表格中
2. 双击编辑单元格内容
3. 调整样式使其与其他行一致

### 修改确认事项文本

1. 找到确认事项的文本块
2. 双击编辑内容
3. 保存修改

## 📞 技术支持

如果遇到问题，请检查：

1. 服务器是否正常运行（`http://localhost:8080`）
2. 浏览器控制台是否有错误信息
3. 模板文件是否有写入权限
4. 网络连接是否正常（GrapesJS 从 CDN 加载）

## 🔗 相关链接

- GrapesJS 官方文档：https://grapesjs.com/docs/
- GrapesJS GitHub：https://github.com/GrapesJS/grapesjs
- ThinkPHP 5.1 文档：https://www.kancloud.cn/manual/thinkphp5_1/

---

**创建时间**: 2025-11-26
**版本**: 1.0.0
