# 女人偶外觀精修

保留 `public/assets/character-third-pants.glb` 作為來源與同光線比較版本。正式預覽載入 `character-female-refined.glb`，未修改男人偶。

## 重建

在專案根目錄，以 Blender 5.2 背景執行 `scripts/refine-female.py`。腳本使用相鄰工作區的 `ToolCache/meshoptimizer-1.2-build/Release/gltfpack.exe`，輸出資產與 JSON 清單。中間檔放在已忽略的 `.character-build/`。

以 `node scripts/test-character.mjs .character-build/authoring.glb` 驗證分層覆蓋、解碼、法線、蒙皮權重、預設中性臉型、十個塑形目標、身體壓縮誤差和衣物背面間距，再執行 `pnpm build`。

## 內容

- 身體曲面細分，保留 UV、材質區域、骨架及每個塑形目標。
- 褲腰曲面修整與膝部、褲腳小幅褶皺；外套與內搭背面增加實際間距，修復原始資產重疊。
- 虹膜頂點色纖維、貼合表面的眉毛與睫毛網格，以及依既有髮型表面配置的細髮。
- 皮膚、嘴唇、指甲、眼睛、髮絲、皮革和織物各自設定反光；保留來源皮膚色彩貼圖，織物與皮革細節使用程式材質。
- 15 個可切換材質分層、三種燈光、原始／精修模型比較及既有穿衣／裸體確認流程。

## 實際限制

這是現有資產的即時外觀精修，並非掃描重建或完整角色重製。皮膚採用少量包覆漫反射近似，沒有宣稱為物理體積次表面散射。眼睛使用表面塗層近似濕潤反光，沒有額外角膜體積。頭髮仍以既有髮片配合細絲網格呈現；本轮未新增表情動畫、布料模擬或動態碰撞。

Blender 可用於資產多角度渲染檢查；離線渲染與網站的 Three.js 光照不完全相同。自動測試使用正式 GLTFLoader 和 MeshoptDecoder 執行 CPU 幾何檢查，不代表所有瀏覽器／GPU 都已完成互動驗收。

## 匯出注意

新建塑形明確使用 `from_mix=False` 並將 `value` 歸零。先匯出未壓縮 GLB，再由 gltfpack 壓縮，保留必要 UV、節點、材質與自訂資料。不要啟用 Blender 的中間 meshopt 壓縮；本次近景檢查發現該路徑會產生曲面瑕疵。
