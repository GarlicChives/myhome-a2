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
**新功能必須同步新增對應斷言**（selftest 目前 27 項）。

## 標準工作流程（每次需求都照做）

1. 先讀 `A2戶型-圖面解析.md`（圖面知識與功能現況）＋本檔陷阱清單。
2. 只改 `tools/app_template.html`（**唯一 source of truth，嚴禁直接改產出 HTML**）。
3. `python tools/build_app.py` 重建 `A2戶型居家模擬.html`（路徑已指向本目錄）。
4. headless Chrome 跑 `?selftest=1` → **27 項全 PASS**；有新功能先補斷言再回到步驟 3。
5. 以人類視角逐張檢視截圖（base / st=3d / st=sel / st=panel / st=tut），確認版面與互動狀態。
6. 更新本檔（斷言數、功能清單）、`A2戶型-圖面解析.md`、auto-memory。
7. Claude in Chrome 擴充每次可再試 `list_connected_browsers`（使用者 profile：`Profile 11`／小譁
   v4578469@gmail.com；至今未連上，成功即可實機操作驗證）。

驗證指令（PowerShell 用 `Start-Process -Wait`，直接 `&` 呼叫常拿不到檔案）：
```
chrome --headless --disable-gpu --screenshot=x.png --window-size=1440,900 --virtual-time-budget=6000 "file:///D:/Desktop/MyHome/A2戶型居家模擬.html?selftest=1[&st=3d|light|grid|sel|panel|tut]"
```
chrome 路徑：`C:\Program Files (x86)\Google\Chrome\Application\chrome.exe`。全 PASS 時 title=ST-PASS。

## 檔案結構

- `A2戶型.dwg` — 原始檔（AC1032，單位＝公分）。唯一真值來源
- `A2戶型.dxf` — ODA 轉出的中繼檔，程式解析都用它
- `A2戶型居家模擬.html` — 主系統（單一自包含檔可上雲分享；功能總表見圖面解析.md）
- `A2戶型列印圖.html` — 手繪列印圖（10cm 格線、原點=玄關牆角 (25,1225)、A3 1:50 / A4 1:75）
- `A2戶型-圖面解析.md` — **先讀這份**：空間構成、尺寸全表、牆厚、審查結論、功能總表
- `tools/` — 重建管線：`extract.py`（DXF→base_cm.svg＋plan_data.json）→ `build_app.py` →
  （列印圖：`build_print.py`→`verify_print.py` 28 筆尺寸全 PASS）；`audit.py` CAD 標示審查
- Python 3.12 + ezdxf 1.4.4；**此機器 pip 無法連 PyPI**
- ODA File Converter：`C:\Program Files\ODA\ODAFileConverter 27.1.0\ODAFileConverter.exe`
  用法：`ODAFileConverter <入資料夾> <出資料夾> ACAD2018 DXF 0 1 <檔名>`

## 互動設計（已定案，勿回退）

- 家具拖曳＝狀態機 free⇄mag⇄stack，遲滯門檻（吸附-2.5cm／脫離-6cm／入疊 min(15cm,半寬)／出疊 40%）。
  **嚴禁二值切換造成的閃爍**。家具磁鐵可突破（推入即疊放、回拖退回貼邊）；牆＝硬阻擋不可突破、
  磁吸 5cm、沿牆滑動、嚴禁覆蓋。
- 禁止懸空：支點只能是地板或家具頂面（settleGravity），拖曳下方物件整疊連動（beginCarry 遞迴）。
- 天花板上限預設 280cm（面板可調），超高整件變紅並退回。
- Shift+點選多選＋R 群組旋轉（繞群組外框中心）；Ctrl+C/V 複製貼上；滾輪換疊放層。
- 選取顯示長寬高：CAD 標註樣式畫在對應邊緣（2D 標註線、3D 邊緣 billboard）。
- 3D 標籤一律 billboard（反向抵銷 rotateX/rotateZ＋反縮放）。
- 教學 Modal：首次進站自動彈出（今日不再顯示存 localStorage 當日字串）、Header「❓ 教學」可重開；
  `?selftest=1` 時不自動彈出（st=tut 例外）。
- 未特別提及時，需求主要針對 3D 檢視（2D 同步但非重點）。

## 圖面關鍵知識（已驗證，勿重推導）

- 平面座標系：cm，原點=可見內容左上；WCS 對應 X0=376137.7685、Ytop=-21196.2788
- 牆厚：外牆/主牆 15cm、室內隔間 10cm
- 外徑鏈：上 130+550=680｜下 220+185+250=655（自玄關角 x=25 起）｜左 170+825+230=1225｜右 885+145+40=1070
- 格線/手繪原點＝玄關牆角 (25, 1225)（使用者習慣：從門口起算）
- DWG 內藏整棟建案圖（全在凍結/關閉圖層，2500+ 圖元）；需要建物脈絡可解凍分析
- 已知標示不清（審查結論）：廚具座標非模數（x=354.527），「124.5」走道實際 124.523、
  且是牆到廚具（牆到牆為 185）；「57.5」端點鉤在廚具角。結構尺寸全部可信

## 陷阱（踩過的坑）

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
