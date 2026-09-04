# AevryndWeb

Aevrynd 助理入口網站，使用 ASP.NET Core MVC（.NET 8）。

目前功能：

- 固定信箱白名單登入
- 八位英數一次性驗證碼
- 60 秒重寄間隔、10 分鐘期限、單次使用與錯誤次數限制
- CSRF、來源檢查、安全 Cookie、CSP 與安全標頭
- Kestrel 僅監聽 `127.0.0.1:8792`
- 可由 HTTPS 反向通道安全公開

## Remote Console

Remote Console 在每次網站程序啟動時預設關閉。它要求原本的擁有者登入、伺服器端 Session／Security Stamp、一次本機配對碼，以及第二次郵件 OTP。控制 grant 的絕對期限為 8 小時、閒置期限為 30 分鐘；成功的文字、鍵盤或滑鼠操作會延後閒置期限，但不會延長 8 小時絕對期限，而且同時最多只有一個有效工作階段。本機開關預設仍為 15 分鐘，明確指定時最多可設為 480 分鐘。

網站程序必須在非系統管理員的 Windows 互動式主控台 Session 與 `Default` input desktop 執行。開啟前，在主電腦網站程序啟動完成後執行：

```powershell
pwsh -File .\AevryndWeb\scripts\Enable-RemoteConsole.ps1 -Minutes 15 -Capabilities screen.read,input.text,keyboard.write,mouse.write
```

腳本只會顯示一次 pairing code，並將短效狀態與 Data Protection 目錄限制為目前使用者、SYSTEM 和 Administrators。`mouse.write` 必須同時啟用 `screen.read`。完成工作或有疑慮時立即執行：

```powershell
pwsh -File .\AevryndWeb\scripts\Disable-RemoteConsole.ps1
```

文字與鍵盤輸入預設只允許 Win32 `Edit`／`RichEdit` 類型且非密碼欄位的前景控制項。Chrome／Edge 僅在本機額外明確加入 `browser.input` capability 時允許；網站無法可靠辨識瀏覽器 renderer 內的密碼欄位，因此頁面會顯示敏感警告，操作人必須自行確認目前焦點。終端機、未知程序或控制項、較高權限視窗與安全桌面仍會安全拒絕。畫面為不落盤、全域低於每秒一張、最高 1280×720 的 JPEG。滑鼠座標必須綁定兩秒內、相同 Per-Monitor-V2 顯示器拓樸的 frame generation。

`shell.execute` 尚未開放。本機腳本不接受此 capability，正式後端也只會回報不可用；必須先完成獨立低權限 Windows 帳號 broker、固定 `pwsh` 雜湊、Job Object、輸出／逾時限制及秘密隔離驗證，不能由網站程序直接啟動 Shell。

機密資料不在版本庫內。Gmail 應用程式密碼必須透過 User Secrets、環境變數或部署主機的安全憑證儲存提供。

## Remote operations telemetry

副機 telemetry 使用不可匯出的 Windows CNG ECDSA P-256 私鑰簽章；安裝只產生可公開傳遞的 enrollment JSON，網站公鑰則由外部設定依 `nodeId` 與 `keyId` 嚴格綁定。私鑰不會進入檔案、命令列、記錄或版本庫。輪替、撤銷、legacy HMAC 相容模式及完整操作方式見 [scripts/Operations-Telemetry.md](AevryndWeb/scripts/Operations-Telemetry.md)。
