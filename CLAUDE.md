# 新家規劃專案（日安TOKYO・A2戶型）

屋主用來規劃新家的專案。核心圖面：`A2戶型.dwg`（10~24F A2戶平面參考圖，左鄰A1右鄰A3）。
產出將**交給統包／設計師施工使用**，也會分享上雲（Google 雲端）；願景是發展成
「上傳 CAD 檔，不懂 AutoCAD 的一般民眾也能模擬居家配置」的服務（保留水電 MEP 圖層擴充性，尚未實作）。
使用者會在不同 session 持續提出需求——每次都照下方工作流程執行。

## 最高原則（凌駕一切，嚴禁妥協）

**所有尺寸絕對必須與 `A2戶型.dwg` 一致，嚴禁任何誤差**（施工依據）。
每次改動後必須跑自動化驗證且全 PASS 才可交付，驗證涵蓋：
2D 量測=CAD 標註、3D 座標往返（<0.01cm）、物件擺放後四向距離、旋轉後距離、
兩點距離、物件與鄰近點（牆/家具）距離、外徑鏈總和。程式化斷言，不可目測了事；
**新功能必須同步新增對應斷言**（selftest 目前 103 項）。自測不可只靠截圖：必須含真實
PointerEvent 拖曳、堆疊、全部規則情境，且涵蓋所有物件種類（含內建物件全規則掃描）。
**測試路徑要含對角/牆角等非軸向情境**（曾因只測軸向漏掉「對角逼近牆角整步退回卡住」的滑動 Bug）。

## Token 節約規則（每個 session 都遵守）

- **讀檔一律先 Grep 定位，再小範圍 Read（offset/limit ±60 行）**；嚴禁整檔或大段掃讀
  `tools/app_template.html`（4900+ 行）、`FEATURES.md`、`A2戶型-圖面解析.md`。
- 功能規格全文在 `FEATURES.md`（依 `##` 節分節）——**只 Grep 本次需求相關的節**。
- 驗證截圖：**例行改動只拍 1 張 badge 截圖（760×1700）**；st 視圖抽驗僅在 UI 版面/主題/Modal
  變動時拍「相關的 2~3 張」，全套 9 張僅大改版跑一次。
- 重現/除錯畫面：優先用注入 script 的 repro（讀 debug 文字），少拍多張全頁截圖；
  需要細節時裁切放大單張，不重拍全頁。
- Claude in Chrome 已連上時：**用 javascript_tool 讀 `document.title`（ST-PASS/ST-FAIL）與
  read_page 文字驗證取代截圖**（文字比圖片省一個數量級 token）；截圖只留人工檢視版面用。

## 標準工作流程（每次需求都照做）

1. 依需求 **Grep `FEATURES.md` 相關節**（功能規格）＋必要時 `A2戶型-圖面解析.md` 相關段
   （圖面知識）＋本檔陷阱清單。不整檔讀。
2. 只改 `tools/app_template.html`（**唯一 source of truth，嚴禁直接改產出 HTML**）。
3. `python tools/build_app.py` 重建 `A2戶型居家模擬.html`（路徑已指向本目錄）。
4. headless Chrome 跑 `?selftest=1` → **82 項全 PASS**；有新功能先補斷言再回到步驟 3。
   注意：此機 Chrome 150 `--dump-dom` 無輸出，驗證用高視窗截圖（--window-size=760,1700）讀 badge；
   `&nb=1` 可隱藏 badge 供人工檢視畫面。
5. UI 版面有變動才抽驗相關 st 視圖截圖（base / st=3d / sel / panel / tut / ver / light / wood / cab / ceil）。
6. 更新本檔（斷言數、功能索引）、`FEATURES.md` 對應節、必要時 `A2戶型-圖面解析.md`、auto-memory。
7. 交付後 `git add -A && git commit`。**2026-08-01 使用者已改為永久授權：「往後做完驗證無誤後
   都可以直接 commit+push+deploy」**——驗證全 PASS 即 push 並以 live URL（headless）重跑 selftest。
8. **Claude in Chrome 已於 2026-07-31 連通**（deviceId 9f8498d7-c392-4dce-a14e-fb05391e325a／
   "Browser 1"）：連線程序＝`list_connected_browsers` → AskUserQuestion 讓使用者選 → `select_browser`
   → `tabs_context_mcp`。詳見下節「實機瀏覽器驗證」。

驗證指令（PowerShell 用 `Start-Process -Wait`，直接 `&` 呼叫常拿不到檔案）：
```
chrome --headless --disable-gpu --screenshot=x.png --window-size=1440,900 --virtual-time-budget=6000 "file:///D:/Desktop/MyHome/A2戶型居家模擬.html?selftest=1[&st=3d|light|grid|sel|panel|tut|ceil|cab]"
```
chrome 路徑：`C:\Program Files (x86)\Google\Chrome\Application\chrome.exe`。全 PASS 時 title=ST-PASS。

## 實機瀏覽器驗證（Claude in Chrome；優先於 headless 截圖）

- **擴充功能不能開 `file://`**（回 "unparseable URL"）→ 先起本機伺服器再連：
  `python -m http.server 8777 --bind 127.0.0.1`（cwd＝D:\Desktop\MyHome，Bash 工具背景執行），
  網址 `http://127.0.0.1:8777/A2%E6%88%B6%E5%9E%8B%E5%B1%85%E5%AE%B6%E6%A8%A1%E6%93%AC.html`。
- **selftest 驗證用 javascript_tool 讀文字，不要截圖**（省 ~10 倍 token）：
  `?selftest=1` → 讀 `document.title`＋`#selftestBadge` 文字，過濾 `FAIL` 開頭行、回報項數。
- **功能驗證同樣走 javascript_tool 回傳物件**（例：新增物件後回 `{尺寸,離地,型式,顏色}`），
  比截圖精準且便宜；截圖只在「使用者抱怨的是外觀」時拍一張，必要時用 `computer.zoom` 裁切放大。
- **⚠ 嚴禁在使用者常用 origin 跑 `?selftest=1`**：selftest 會 `localStorage.clear()`，
  在 live URL（garlicchives.github.io）或使用者慣用的 file:// 頁面上跑會**清掉他的存檔配置**。
  一律用 `127.0.0.1:8777` 這個獨立 origin 做測試（localStorage 分離、不影響使用者資料）。

## 檔案結構

- `A2戶型.dwg` — 原始檔（AC1032，單位＝公分）。唯一真值來源
- `A2戶型.dxf` — ODA 轉出的中繼檔，程式解析都用它
- `A2戶型居家模擬.html` — 主系統（單一自包含檔可上雲分享）
- `A2戶型列印圖.html` — 手繪列印圖（10cm 格線、原點=玄關牆角 (25,1225)、A3 1:50 / A4 1:75）
- `FEATURES.md` — **功能規格全文（已定案勿回退）**，依 `##` 節 Grep 讀取
- `A2戶型-圖面解析.md` — 空間構成、尺寸全表、牆厚、審查結論
- `tools/` — 重建管線：`extract.py`（DXF→base_cm.svg＋plan_data.json）→
  `add_counter_obstacle.py`（流理台外框→WALLS，座標由抓點推導；**重跑 extract 後必須再跑**）→
  `build_app.py`；（列印圖：`build_print.py`→`verify_print.py` 28 筆尺寸全 PASS）；`audit.py` CAD 標示審查
- Python 3.12 + ezdxf 1.4.4；**此機器 pip 無法連 PyPI**
- ODA File Converter：`C:\Program Files\ODA\ODAFileConverter 27.1.0\ODAFileConverter.exe`
  用法：`ODAFileConverter <入資料夾> <出資料夾> ACAD2018 DXF 0 1 <檔名>`

## 功能索引（規格細節→FEATURES.md 同名節）

物件基本規則（磁吸/堆疊/滑動）｜臨邊支點規則｜天花板｜懸停尺標｜主題｜物件顏色｜備註｜
系統內建物件（22 種＋人物；統一下拉＝唯一新增入口，選取自動帶入表單；鞋子=一雙）｜
總筆記面板（左側；櫃體備註僅存在時顯示）｜櫃體前板（預設刪除、可加回設玻璃；內徑含前板厚精準）｜
管柱掛件（🪝 Modal 1D 吊桿檢視：衣服/外套/廚具/鍋子，拖曳/覆蓋調換；管柱無櫃體編輯）｜
材質（玻璃/洞洞板/不鏽鋼）｜風格系統（32 種、styleSel、語意角色換色、覆蓋全部顏色含地板）｜擬真外皮（addCyl 真圓柱 N=10：電鍋/垃圾桶/掛鍋；rr 圓角面；
電鍋頂蓋固定不鏽鋼色；**圓弧角功能已依使用者要求移除**）｜
櫃內物品編輯（共用尺寸/顏色欄 ciAdd*：選物品=編輯、選格=新增輸入；超界禁止還原警示；放置格內徑標示扣板厚）｜
管柱（預設 L、新增即釘天花板、#9aa3ad、管徑 3.4=25A）｜匯入換皮規則｜
上一步/下一步（Ctrl+Z 復原、Ctrl+Y 重做；主視圖＋櫃體 Modal 各自獨立）｜垂直旋轉（寬↔高互換、V 鍵）｜
選取懸浮功能列（3D 顯示於整疊最高點上方）｜3D 直接操作（Alt+拖曳離地、PgUp/PgDn、薄件隱形把手）｜
櫃體編輯 Modal（殼板/隔板/放置格/材質）｜多選複製｜平移（左+右鍵）｜鍵盤微調 0.5cm｜
尺寸標註/3D billboard｜教學 Modal｜版本管理/匯出匯入（完整狀態含天花板）｜
高度上限=天花板｜流理台障礙｜門口 DOORS｜人物。
未特別提及時，需求主要針對 3D 檢視（2D 同步但非重點）。

## 部署

GitHub Pages **https://garlicchives.github.io/myhome-a2/**（repo：GarlicChives/myhome-a2，
`index.html` 與主檔同內容、build_app.py 一併輸出）。gh CLI：`C:\Program Files\GitHub CLI\gh.exe`
（帳號 GarlicChives＝使用者個人帳號）；git 需 `http.sslBackend=schannel`（公司網路 SSL 檢查）＋
`gh auth setup-git` 憑證。改版後 push 即自動重新部署（約 1 分鐘），需以 live URL 重跑 selftest 驗證。
**push 前 live 版可能落後多個 commit——使用者回報「舊 Bug 還在」時，先確認他測的是本地檔還是 live URL，
並確認本地檔已重新整理（F5；長開的舊分頁跑的仍是舊 JS）。**

## 圖面關鍵知識（已驗證，勿重推導）

- 平面座標系：cm，原點=可見內容左上；WCS 對應 X0=376137.7685、Ytop=-21196.2788
- 牆厚：外牆/主牆 15cm、室內隔間 10cm
- 外徑鏈：上 130+550=680｜下 220+185+250=655（自玄關角 x=25 起）｜左 170+825+230=1225｜右 885+145+40=1070
- 格線/手繪原點＝玄關牆角 (25, 1225)（使用者習慣：從門口起算）
- DWG 內藏整棟建案圖（全在凍結/關閉圖層，2500+ 圖元）；需要建物脈絡可解凍分析
- 已知標示不清（審查結論）：廚具座標非模數（x=354.527），「124.5」走道實際 124.523、
  且是牆到廚具（牆到牆為 185）；「57.5」端點鉤在廚具角。結構尺寸全部可信

## 陷阱（踩過的坑）

- **selftest 以 pev 派發指標事件前，必須「當下」重新查詢目標節點**：addFurniture/refreshAll 會
  rebuildBoxes 整個重建 boxHost，先前抓的元素已脫離文件 → 事件不冒泡、靜默失敗（drag3F 不會設）。
- **Claude in Chrome javascript_tool 注入一律包 IIFE**：頂層 `var el=...` 會蓋掉頁面全域函式
  （曾蓋掉 `el()` 造成 redrawFurniture2d 拋例外，誤判為產品 Bug 追了半小時）。
- **實機 computer 工具座標＝截圖座標（1568 寬），頁面 CSS 寬 1920 → 換算 ×(1568/1920)**；
  CDP 合成 scroll 不會觸發頁面 wheel 縮放（要測縮放用 JS 派發 WheelEvent）。
- **Modal 內的按鈕若放在會 setPointerCapture 的 3D 區（#cabView）內，click 會被攔截 → 按鈕完全沒反應**：
  cabView 的 pointerdown 必須先 `if (e.target.closest('#cabTools')) return;` 才不會捕獲指標。
  **教訓：自測點按鈕不可只用 `el.click()`（會略過指標路徑而假 PASS），必須送 pointerdown→pointerup→click
  的真實序列**（realClick），才能重現使用者實際操作。
- **牆面線被門窗開口切成多段（38 個中段接點）**：pointInObb 必須把「點在物件邊上 ±0.05cm」
  視為接觸而非包含，否則物件貼牆會被誤判碰撞、卡在磁吸距離外進不去。
- planeFromScreen 的 Newton 收斂門檻須 0.001px/12 次迭代，否則 3D 座標往返誤差 >0.01cm。
- ezdxf：`draw_entities()` 不套背景/色彩策略要用 `draw_layout()`；DIMENSION 顏色解析為白色；
  SVG class 名是十六進位（C1..CF..）；文字型式須改 `msjh.ttc` 才有中文。
- selftest 會 `localStorage.clear()` 並重建測試家具；斷言用的座標（fA 茶几等）在測試間有先後相依，
  新增測試放在檔尾、留意當下家具位置。

## 使用者偏好

- 溝通用繁體中文；重視精確與可驗證性，交付要附驗證證據（PASS 清單＋截圖）
- 檔案需可上雲分享（單一自包含 HTML、無外部資源）
- 手繪習慣從玄關起算；列印要 100% 實際大小
