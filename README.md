# AevryndWeb

Aevrynd 助理入口網站，使用 ASP.NET Core MVC（.NET 8）。

目前功能：

- 固定信箱白名單登入
- 八位英數一次性驗證碼
- 60 秒重寄間隔、10 分鐘期限、單次使用與錯誤次數限制
- CSRF、來源檢查、安全 Cookie、CSP 與安全標頭
- Kestrel 僅監聽 `127.0.0.1:8792`
- 可由 HTTPS 反向通道安全公開

機密資料不在版本庫內。Gmail 應用程式密碼必須透過 User Secrets、環境變數或部署主機的安全憑證儲存提供。
