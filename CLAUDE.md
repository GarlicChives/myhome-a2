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
**新功能必須同步新增對應斷言**（selftest 目前 78 項）。自測不可只靠截圖：必須含真實
PointerEvent 拖曳、堆疊、全部規則情境，且涵蓋所有物件種類（含 14 種內建物件全規則掃描）。
**測試路徑要含對角/牆角等非軸向情境**（曾因只測軸向漏掉「對角逼近牆角整步退回卡住」的滑動 Bug）。

## 標準工作流程（每次需求都照做）

1. 先讀 `A2戶型-圖面解析.md`（圖面知識與功能現況）＋本檔陷阱清單。
2. 只改 `tools/app_template.html`（**唯一 source of truth，嚴禁直接改產出 HTML**）。
3. `python tools/build_app.py` 重建 `A2戶型居家模擬.html`（路徑已指向本目錄）。
4. headless Chrome 跑 `?selftest=1` → **78 項全 PASS**；有新功能先補斷言再回到步驟 3。
   注意：此機 Chrome 150 `--dump-dom` 無輸出，驗證用高視窗截圖（--window-size=1100,1500）讀 badge。
5. 以人類視角逐張檢視截圖（base / st=3d / st=sel / st=panel / st=tut / st=ver / st=light / st=wood / st=cab），確認版面與互動狀態。
6. 更新本檔（斷言數、功能清單）、`A2戶型-圖面解析.md`、auto-memory。
7. 交付後 `git add -A && git commit`。**永久規則：`git push` 與部署必須等使用者明確下令才可執行**
   ——commit 完成後回報「已就緒，等指令 push」，收到指令才 push 並以 live URL 重跑 selftest。
8. Claude in Chrome 擴充每次可再試 `list_connected_browsers`（使用者 profile：`Profile 11`／小譁
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
- `tools/` — 重建管線：`extract.py`（DXF→base_cm.svg＋plan_data.json）→
  `add_counter_obstacle.py`（流理台外框→WALLS，座標由抓點推導；**重跑 extract 後必須再跑**）→
  `build_app.py`；（列印圖：`build_print.py`→`verify_print.py` 28 筆尺寸全 PASS）；`audit.py` CAD 標示審查
- Python 3.12 + ezdxf 1.4.4；**此機器 pip 無法連 PyPI**
- ODA File Converter：`C:\Program Files\ODA\ODAFileConverter 27.1.0\ODAFileConverter.exe`
  用法：`ODAFileConverter <入資料夾> <出資料夾> ACAD2018 DXF 0 1 <檔名>`

## 互動設計（已定案，勿回退）

- **名詞定義（與使用者對齊）**：「物件」＝家具/家電/盛板/放置物等，可設長寬高與名稱（**名稱可留空**），
  受「物件規則」約束：磁吸反饋、不可覆蓋牆面、不可懸空（臨邊支點）、可堆疊、總高不可超過天花板。
- 家具拖曳＝狀態機 free⇄mag⇄stack，遲滯門檻（吸附-2.5cm／脫離-6cm／入疊 min(15cm,半寬)／出疊 40%）。
  **嚴禁二值切換造成的閃爍**。家具磁鐵可突破（推入即疊放、回拖退回貼邊）；牆＝硬阻擋不可突破、
  磁吸 5cm、沿牆滑動、嚴禁覆蓋。**阻擋滑動＝逐軸二分推進（maxReach，收斂<0.02cm 後磁吸貼齊）**，
  嚴禁退回離散候選點——舊版整步退回 lastGood 曾造成對角逼近牆角卡在殘留間隙（已根治+斷言防回歸）。
- 不可懸空＝**臨邊支點規則**（2026-07-30 改版，取代舊「支點只能是地板/家具頂面」）：物件**任一臨邊**
  有支點即可停留——地板、其他物件（頂/底/側面貼合 ±0.25cm）、天花板（頂到 CEIL）、牆面（側貼＝可釘固定）。
  settleGravity 先錨定（底=地板、側貼牆 wallTouch、頂=天花板 ceilTouch），再與已支撐物件面接觸連鎖
  （objContact BFS），其餘由低到高落至最高支撐面；拖曳中貼牆/頂天花板亦保持高度（dragTo）。
  拖曳下方物件整疊連動（beginCarry 遞迴）。
- **天花板（面板獨立「天花板」區）**：高度預設 280cm（#fCeil，移出物件區），超高整件變紅並退回；
  **「顯示天花板」可切換 3D 極半透明平面 #ceilPlane**（z=CEIL、pointer-events:none 不擋點擊、
  附 billboard 標籤「天花板 N cm」於 #vgHost；updateCeilPlane 由 setMode/refreshAll/高度變更呼叫）。
  物件釘天花板能力＝臨邊支點規則之 ceilTouch（頂到 CEIL ±0.25cm 即固定，settleGravity/dragTo 皆有）。
- 懸停尺標＝水平四向距離（2D/3D、含物件距離、距門口）＋**垂直臨近兩點距離（僅 3D＝非正俯瞰視角）**：
  懸停物件→頂面↑至上方物件底/天花板、底面↓至下方物件頂/地板；懸停平面→該點↑至上方物件底/天花板。
  實作：updateVGuides→#vgHost（獨立於 boxHost，rebuild 不清除）、.vg-line 世界垂直線僅繞 z 反轉面向鏡頭、
  標籤「↕ N」billboard；updateBillboards 以 world.querySelectorAll 統一更新。
- 主題＝三預設（黑/白/**淺暖木紋**）＋調色盤自訂底色（header #themeColor）：applyTheme 以亮度 lum>0.5
  自動判定亮暗 → 格線與公分數（guide/dim/m/fdim 文字）切換高對比色；木紋＝.wood class（CSS 覆蓋
  **必須放在 __LIGHT_CSS__ 之後**）＋SVG pattern #woodPat 作圖底；主題存 localStorage a2home_theme。
  **主題只變更 bgRect（平面圖底）；平面圖以外（stage/scene3d 背景）固定黑色**，
  因此外徑鏈（edim，畫在圖外）恆用亮色不隨主題。**st=light 依賴白色預設按鈕 id=btnTheme，勿改 id**。
- 物件顏色＝調色盤（#fColor input type=color，取代舊 16 色格）：選取物件即時套用、面板同步顯示 hex。
- **備註**：物件 f.note（面板 #fNote textarea）與櫃體 f.cab.note（Modal #cabNote）皆為自由文字，
  隨存檔/匯出/複製；清單以 title 顯示、名稱後加 📝，3D 名稱標籤亦加 📝。hasCab 含 note。
- **系統內建物件 16 種**（BUILTINS：桌子/冰箱/隔板60×30×2/床/沙發/鞋櫃/衣櫃/行李箱/登機箱/小椅子/
  小餐邊推車/垃圾桶/投影機/洗衣籃/**鞋子 24×10×9（腳長 24cm）**/**管柱 120×8×60**；同名尺寸取自 A2居家配置_0849.json，冰箱 json 值 20×60×195 不合理
  改用 60×70×180；**鞋櫃 2026-07-31 依使用者指定改 64×32×200**）：內建於程式、不受存檔影響；
  **本質＝一般物件**（可自訂長寬高、受全部物件規則）；
  3D 以 SKIN3D 多部件外皮呈現（比例縮放）。**正面＝+y（預設視角近側）**：門面/櫃體開口/沙發座向皆同。
  **面板改為統一下拉選單 #builtinSel＋「➕ 加入」**（物件已多；含男/女主人 person:m|f，共 18 個 option，
  舊 #builtinGrid/btnMan/btnWoman 已移除）。
- **管柱（k=pipe）**：f.pipe='I'|'L'|'U'（面板 #fPipe）＋管徑 f.pipeT（#fPipeT，預設 PIPE_T=8）；
  pipeParts(f) 推導部件——**直＝沿最長邊一根（w≥h 為水平貼頂、否則垂直）、L＝頂部橫段＋一端垂直段、
  U＝頂部橫段＋兩端垂直段**（依使用者提供的天花板轉折方管照片）；3D 走 SKIN3D.pipe、2D 俯視畫實際管段投影。
  **碰撞/磁吸仍用整體 OBB**（與所有既有物件規則一致）；固定方式＝臨邊支點：只要一端貼天花板或牆即釘住，
  兩端皆無支點才落地。
  **匯入/載入存檔/還原版本時，名稱同內建物件者自動換皮（applySkins）——已有櫃體修改（hasCab）者除外**。
  **內建物件只要有櫃體修改儲存（closeCab 時 hasCab 為真）→ delete f.skin，外觀改為櫃體殼板**（2026-07-31
  改版，取代舊「SKIN_INNER 桌子保留外皮」機制——SKIN_INNER 已整個移除，所有物件進櫃體編輯一律殼板模型）。
- **上一步（復原）**：histStack（saveState→pushHistory 去重、上限 100）、Ctrl+Z 或 header「↩ 復原」；
  undo 以快照整批替換 furniture（**測試中 undo 後所有物件參照需 byId 重綁**）。
  **櫃體編輯 Modal 開啟中 pushHistory 凍結**：closeCab 後 refreshAll 記一步 → 主視圖「復原」＝整段櫃體
  編輯一步退回（外皮/cab 一起還原）。**Modal 內自有上一步 cabHist/cabPush/cabUndo**（↩ 上一步鈕；
  Ctrl+Z 於 Modal 開啟時路由至 cabUndo）；cabCommit()＝renderCab+syncCabPanel+refreshAll+cabPush，
  Modal 內所有完成操作走它。
- **選取懸浮功能列 #selBar**（單選時顯示於物件上方）：🗄 櫃體／⟳90°／⧉ 複製／🗑 刪除（人物無櫃體鈕）。
- **櫃體編輯 Modal（90vw×90vh）**：物件變空心殼（殼厚 CAB_TS=2cm、正面 +y 開放＝開口、無前板）＋隔板＋櫃內物品。
  f.cab={t(隔板厚度預設 2、範圍 0.4~3), parts:[{dir:'h'|'v',pos,t,color?,mat?}], items:[{w,d,h,x,y,z,skin?,...}],
  noBottom/noTop/noLeft/noRight/noBack, sc:{bottom/top/left/right/back:{color,mat}}}。
  **殼板五片（底/頂/左/右/背 CAB_BOARDS）與所有隔板皆為物件、皆可選取刪除**：3D 點選（點擊映射於
  內部空間之外＝選殼板、之內＝選放置格；endCabPtr 位移<5px 才算點擊）或側欄列表點選；刪除＝設 noX 旗標，
  恢復靠側欄 cabShellB/T/L/R/K 鈕；刪底板＝內底直接是地板（檯面下擺放）——內部座標原點＝內左緣/內底
  （cabInner 回傳 x0/z0/y0 偏移），切換殼板時物品/隔板座標平移補償、絕對位置不變（noBack 只改 idp 無補償）；
  hasCab 含旗標與 sc；closeCab 用 hasCab 判斷保留。
  **板材顏色/材質**：每片殼板（cab.sc[key]）與隔板（p.color/p.mat）可各自設定顏色＋特別材質——
  **玻璃 glass＝半透明 rgba 0.32（無自訂色時預設 #8ecae6）、洞洞板 peg＝radial-gradient 圓洞紋**
  （boardFill/cabShellFill；Modal、主視圖 3D、2D 俯視同步；CSS background 可含漸層層）。
  **放置物品可選內建物件**（#cabAddKind 下拉：自訂＋16 種；item 帶 skin 以外皮渲染於 Modal 與主 3D）；
  **尺寸一律取側欄輸入框當下值（#ciAddW/D/H＋#ciAddColor）**——選內建種類只是把其預設尺寸帶入輸入框
  （change 事件；測試若直接設 value 需自行 dispatch change），使用者可再改。
  **Modal 右上角工具列 #cabTools（位於 #cabView 內）：↩ 上一步／✔ 完成儲存（closeCab）／✕ 取消（cancelCab
  ＝回到 cabHist[0] 開啟當下狀態並關閉）**；**點擊 Modal 外不再關閉**（已移除背景 click 關閉，避免誤觸遺失編輯）；
  **Delete 鍵刪選取中的隔板**（其次殼板→物品）；Modal 開啟時主視圖快捷鍵（R/方向鍵/Ctrl+C/V）一律不作用。
  櫃體備註 f.cab.note（#cabNote）。
  **放置物品新增規則（2026-07-31）**：須先點擊櫃內空白格選取「放置格」（cabCells＝隔板切出的網格、
  綠虛線高亮、cabSelCell 存 {xi,zi} 索引），且 cabCellCheck 過關（尺寸放得進格＋體積 ≤ 格剩餘體積＝
  格空間−已放物品體積和），否則拒絕新增；**同格已有物品自動排列 cabArrangeCell**：可並排（Σ寬≤格寬）
  ＝平均間隔擺放，否則堆疊且**較大尺寸（體積降冪）一律在下方**，兩者皆放不下＝退回原位並拒絕。
  隔板新增自動延伸至內徑並平均分配（span*(i+1)/(n+1)＝由中間算起不貼邊）、可拖曳/輸入調位
  （clamp 僅限內徑範圍；**與同向隔板重疊＝整片變紅警示、放開退回**，v↔h 十字相交合法）；
  **移動水平隔板時其頂面上物品（含堆疊遞迴 cabItemsOn）連動位移**，物品壓到其他隔板也紅+退回。
  物品規則特例：**下方必有支點（不會釘牆）**＝櫃底/隔板頂/其他物品頂（cabItemFloor＋cabSettleItems，
  掛在 settleGravity）；物品可互疊但總高不可超上方隔板（超過→cabItemBad 紅）；物品互相重疊＝紅。
  距離（cabItemDists）精準計入內徑、所有隔板厚度與其他物品；放不下（cabItemBad）整件變紅+放開退回。
  **懸停鄰近點規則（Modal 內，與主視圖 3D 統一＝六向：左右上下＋前後）**：懸停物品/隔板/櫃內任意
  空白點（cabPlaneFromScreen 反解深度中線平面）皆顯示鄰近距離（cabPointDists／cabItemDists 含
  front/back：開口側=前、背板側=後）。**主視圖 3D 懸停**：物品面標 data-ci → 顯示該物品六向距離標籤；
  懸停櫃體顯示內部空間（updateCabGuides，標籤文字＝「內部 W×D×H」）。
  cab 資料隨 furniture 存檔/匯出/複製；主 2D 顯內徑虛線框＋垂直隔板、主 3D 空心渲染（重疊隔板紅）。
  Modal 自有 3D（cabCam/cabPt 與 fwd3d 同構數學，供拖曳軸投影與懸停反解）。
- Shift+點選多選＋R 群組旋轉（繞群組外框中心）；Ctrl+C/V 複製貼上；滾輪換疊放層。
- **左+右鍵同時按住拖曳＝平移整張平面圖**（2D 移 viewBox、3D 移 cam.px/py，軸心/角度/縮放不變）：
  進行中的家具拖曳/旋轉即刻取消退回原位（abortActiveDrag）；右鍵單獨拖曳＝平移（2D/3D 一致）、
  右鍵不啟動家具拖曳、stage/scene3d 均 preventDefault contextmenu。
- **鍵盤方向鍵微調選取物件 0.5cm/步**（nudgeSel）：直接位移不經磁吸（可突破磁鐵誤判），
  但不可覆蓋牆面/其他物件（違者整步阻擋+提示）；上方堆疊 pileAbove 連動；INPUT 聚焦或櫃體 Modal 開啟時不作用。
- 選取顯示長寬高：CAD 標註樣式畫在對應邊緣（2D 標註線、3D 邊緣 billboard）。
- 3D 標籤一律 billboard（反向抵銷 rotateX/rotateZ＋反縮放）。
- 教學 Modal：首次進站自動彈出（今日不再顯示存 localStorage 當日字串）、Header「❓ 教學」可重開；
  `?selftest=1` 時不自動彈出（st=tut 例外）。
- 版本管理「💾 版本」：localStorage 多版本另存/還原/刪除（上限 30）；配置隨時自動儲存（重開機續編）。
- 高度上限＝天花板：新增即截斷；選取後右側輸入即時所見即所得套用（liveApply），
  改高度時堆疊上方物件隨頂面位移、整疊頂不可超過 CEIL（setHeight/pileAbove）。
- 流理台（廚具）外框＝障礙物（walls 內 x354.53~414.53/y1010~1170 四段，由 add_counter_obstacle.py 加入）；
  洗手槽內框為純圖面、嚴禁進 WALLS。家具面板預設開啟。
- 門口（DOORS）＝牆面共線群組 40~160cm 缺口自動推導（玄關大門 y1225/x130~230、主臥門、
  兩衛浴門、臥室中門）；懸停/拖曳家具時顯示「距門口 N」（OBB↔門段精確距離，4m 內、隨懸停清除）。
- 人物（kind='person'）：👨男主人 藍#2f6fd6 171cm/75kg、👩女主人 粉#f48fb1 154cm/48kg。
  可拖曳；永遠 z=0（不可離地）；不進磁吸/疊放；與任何物件/牆互為硬阻擋（dragBlocked）。
  3D 以身體＋頭部兩方塊呈現；清單與邊緣標籤顯示 身高/體重。
- 部署：GitHub Pages **https://garlicchives.github.io/myhome-a2/**（repo：GarlicChives/myhome-a2，
  `index.html` 與主檔同內容、build_app.py 一併輸出）。gh CLI：`C:\Program Files\GitHub CLI\gh.exe`
  （帳號 GarlicChives＝使用者個人帳號）；git 需 `http.sslBackend=schannel`（公司網路 SSL 檢查）＋
  `gh auth setup-git` 憑證。改版後 push 即自動重新部署（約 1 分鐘），需以 live URL 重跑 selftest 驗證。
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




