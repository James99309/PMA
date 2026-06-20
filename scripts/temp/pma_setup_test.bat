@echo off
echo Writing PMA MCP config...
echo.
mkdir "%APPDATA%\Claude" 2>nul
(
echo {
echo   "mcpServers": {
echo     "pma": {
echo       "url": "https://pma-mcp.jamesgpone.win/mcp?token=cp-5-rNuUMqNfceEjwk__VIvdy7VI-UiIP-Xn"
echo     }
echo   }
echo }
) > "%APPDATA%\Claude\claude_desktop_config.json"
if %errorlevel% equ 0 (
    echo Done! Please restart Claude Desktop.
) else (
    echo Failed! Error: %errorlevel%
)
pause
