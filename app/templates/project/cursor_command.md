/* Cursor:

请遍历整个 `templates/project/` 目录下的所有 `.html` 文件，将所有自定义按钮（<button> 或 <a>）统一替换为 ui.render_button 宏调用。

要求如下：
- 使用 {{ ui.render_button(...) }} 形式，保留文字、href、type、icon 等原有属性。
- 移除 class（如 btn、btn-primary 等）。
- 如页面中未引入 {% import 'ui_helpers.html' as ui %}，请自动添加。
- 仅限处理 `templates/project/` 目录，不要修改其他模块文件。

请先列出将要修改的文件清单供我确认。
*/