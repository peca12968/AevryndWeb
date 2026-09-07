# Aevrynd 網站內容與資料邊界

更新基準：2026-09-06，台北時間 UTC+8。本輪僅更新文字，未部署、未調整授權或資料程式。

## 現行架構

主機統籌引擎實作、檔案責任、整合、視覺驗收與唯一 Git 提交。主機模型標示為「使用者設定 GPT-6 Astra，中；非執行偵測」。台中與桃園是按需 CPU／GPU 測試資源，不再負責 Codex／Qwen 或 GitHub 任務輪詢，不修改主來源、不自行挑工作。

兩台副機已安裝按需非同步測試服務，支援簽章狀態、簽章證據與視覺影像回收；台中另具 Gameplay 視覺 preset，桃園具 Release／Visual preset。個別工作仍須以 job receipt 判斷，服務顯示 idle 不代表曾經通過測試。完整 Demo 分數維持 34／100，近期目標至少 70／100，v1.4 未發布。

## 頁面配置

| 頁面 | 誰可看 | 用途與內容 | 資料來源 | 已完成／待完成 |
|---|---|---|---|---|
| 首頁／登入 | 公開 | 引擎目標、三機分工示意、OTP（一次性驗證碼）入口 | 靜態文案、既有登入 API | 文案移除副機 Qwen 與靜態 ONLINE 宣稱；不變更信箱授權 |
| Portal 管理控制台 | 既有 AdminPolicy 管理者 | 連到 Operations／RemoteConsole，說明按需測試 | 靜態文案、既有身分判定 | 不把卡片裝飾當成機器在線證據 |
| Showcase 開發展示 | 公開 | 歷史影片、版本演進、角色預覽、三機架構與引擎分層、目前限制 | 既有媒體清單、歷史來源說明、主代理核對的最新 CPU 狀態 | 三機 SVG 文字已改；仍待新來源 11-shot／影片與實際評分，不以CPU測試代替 |
| Operations 主機與工作紀錄 | 既有 OperationsPolicy 授權帳號 | 硬體、使用率採樣、工作摘要、完成與未通過紀錄 | 現有 Snapshot／Schedule／Dispatch JSON 供應者；SQL RemoteTestRuns 已有收據但UI尚未完整接入 | 明列資料遷移中；待讀取SQL真實job、開始/完成/失敗/退出碼/來源SHA與證據；不得從輪詢時間創造活動 |
| RemoteConsole 管理者遠端操作 | 既有 AdminPolicy，另需本機開關與控制授權 | 操作主機桌面；明確區別副機固定測試入口 | 既有 RemoteConsoleViewModel／控制 API | 文案更新；不增加Shell、鍵盤或任何授權 |
| 共用頁首／頁尾 | 隨頁面 | 引擎開發品牌、公開展示導覽 | 靜態文案 | 移除無實測的「安全通道已啟用」宣稱 |
| Privacy 資料使用說明 | 公開 | 說明登入資料、測試紀錄、遠端操作與公開素材的用途 | 既有 HomeController.Privacy 與靜態 View | 已替換預設文案；保存期限與刪除程序仍待管理者確認，不宣稱已有自動刪除 |

## 保留的資料與未完成項

- 本輪保留所有 DOM id、data binding、表單、Razor授權條件及JavaScript來源。
- Operations 的動態 `hardware.Model`、`Role`、`ModelSource` 和 JS snapshot 文案可能仍帶入舊 sol／派工資訊；頁面已加醒目說明，但須後續修正資料來源，不能以靜態文字假裝已清除。
- 現有 Showcase 的歷史版本及技術切片保留為歷史敘述；不得升格為目前候選完整通過。新增「名詞中文對照」章節連結與四組可展開說明，涵蓋硬體、場景、渲染、測試與發布用語；不更動歷史數字或通過範圍。
- 遠端工作頁沿用既有時限與能力標示；網站文案工作不授權修改安全機制。RemoteConsole 現有 ToLocalTime 寫法仍需後續統一到 PortalTime，這輪未改資料邏輯。
- 原有裝飾燈／進度軌不代表即時遙測；文字已區分架構示意。
- 後續圖像下載需保留 job 識別、輸入雜湊、逐檔 SHA-256 及來源 receipt。將收據寫入 SQL 不等於 Operations 已顯示，也不等於 Showcase 已更新。

## 交付驗證

主代理完成 Release publish；角色、部署與 Operations 範圍 19／19 通過，排除兩個必須外掛 `AEVRYND_DISPATCH_FIXTURE` 的錄製資料測試後，其餘完整套件 220／220 通過且無警告。外掛 fixture 未提供時不把該兩項列為產品通過證據。

正式內容已由交易式部署切換至 IIS `127.0.0.1:8080`，並完成本機、外網、目錄 ownership、ngrok 映像與 rollback 契約驗證。Showcase 外網 200；指定第三版 GLB 為 25,717,300 bytes，外網 SHA-256 `9C98378086DE3128119E6BEBA2531D5A37AAA70B594E0FA3859FD93CA63FE838`。目前角色工作室已提供同一模型的臉部／全身視角、360° 環繞、實際 morph 滑桿與上衣／裸體切換；Gameplay 引擎整合仍待後續驗收。
