# AevryndWeb

Aevrynd 遊戲引擎開發歷程網站的 ASP.NET Core MVC 版本。網站保留 3D 角色檢視、成年內容確認、裸體切換二次確認，以及以 SQL Server 儲存的在線人數與瀏覽人次。

## 本機執行

1. 啟動 LocalDB：`sqllocaldb start MSSQLLocalDB`。
2. 執行 `dotnet run --project AevryndWeb/AevryndWeb.csproj`。
3. 開啟終端顯示的本機網址。

網站使用既有的 `Aevrynd` 資料庫。可在 SSMS 連線到 `(localdb)\MSSQLLocalDB` 後查看 `SiteOnlineSessions` 與 `SitePageViews`。

## IIS

以系統管理員身分執行 `scripts/Install-Iis.ps1`。腳本會發布網站、建立 IIS 應用程式集區與網站、套用檔案權限，並授權該應用程式集區存取 SQL Server。
