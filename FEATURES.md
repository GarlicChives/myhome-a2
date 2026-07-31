# 功能規格全文（已定案，勿回退）

> 本檔＝`tools/app_template.html` 全部互動功能的定案規格。
> **改某功能前，只 Grep 讀取對應的 `##` 節，嚴禁整檔讀入**（token 節約）。
> 新增/修改功能後必須同步更新本檔對應節與 CLAUDE.md 的功能索引。

## 名詞定義與物件基本規則

- 「物件」＝家具/家電/盛板/放置物等，可設長寬高與名稱（**名稱可留空**），
  受「物件規則」約束：磁吸反饋、不可覆蓋牆面、不可懸空（臨邊支點）、可堆疊、總高不可超過天花板。
- 家具拖曳＝狀態機 free⇄mag⇄stack，遲滯門檻（吸附-2.5cm／脫離-6cm／入疊 min(15cm,半寬)／出疊 40%）。
  **嚴禁二值切換造成的閃爍**。家具磁鐵可突破（推入即疊放、回拖退回貼邊）；牆＝硬阻擋不可突破、
  磁吸 5cm、沿牆滑動、嚴禁覆蓋。**阻擋滑動＝逐軸二分推進（maxReach，收斂<0.02cm 後磁吸貼齊）**，
  嚴禁退回離散候選點——舊版整步退回 lastGood 曾造成對角逼近牆角卡在殘留間隙（已根治+斷言防回歸）。

## 臨邊支點規則（不可懸空）

- 2026-07-30 改版，取代舊「支點只能是地板/家具頂面」：物件**任一臨邊**有支點即可停留——
  地板、其他物件（頂/底/側面貼合 ±0.25cm）、天花板（頂到 CEIL）、牆面（側貼＝可釘固定）。
  settleGravity 先錨定（底=地板、側貼牆 wallTouch、頂=天花板 ceilTouch），再與已支撐物件面接觸連鎖
  （objContact BFS），其餘由低到高落至最高支撐面；拖曳中貼牆/頂天花板亦保持高度（dragTo）。
  拖曳下方物件整疊連動（beginCarry 遞迴）。

## 天花板

- 面板獨立「天花板」區：高度預設 280cm（#fCeil，移出物件區），超高整件變紅並退回；
  **「顯示天花板」可切換 3D 極半透明平面 #ceilPlane**（z=CEIL、pointer-events:none 不擋點擊、
  附 billboard 標籤「天花板 N cm」於 #vgHost；updateCeilPlane 由 setMode/refreshAll/高度變更呼叫）。
  物件釘天花板能力＝臨邊支點規則之 ceilTouch（頂到 CEIL ±0.25cm 即固定，settleGravity/dragTo 皆有）。

## 懸停尺標

- 水平四向距離（2D/3D、含物件距離、距門口）＋**垂直臨近兩點距離（僅 3D＝非正俯瞰視角）**：
  懸停物件→頂面↑至上方物件底/天花板、底面↓至下方物件頂/地板；懸停平面→該點↑至上方物件底/天花板。
  實作：updateVGuides→#vgHost（獨立於 boxHost，rebuild 不清除）、.vg-line 世界垂直線僅繞 z 反轉面向鏡頭、
  標籤「↕ N」billboard；updateBillboards 以 world.querySelectorAll 統一更新。

## 主題

- 三預設（黑/白/**淺暖木紋**）＋調色盤自訂底色（header #themeColor）：applyTheme 以亮度 lum>0.5
  自動判定亮暗 → 格線與公分數（guide/dim/m/fdim 文字）切換高對比色；木紋＝.wood class（CSS 覆蓋
  **必須放在 __LIGHT_CSS__ 之後**）＋SVG pattern #woodPat 作圖底；主題存 localStorage a2home_theme。
  **主題只變更 bgRect（平面圖底）；平面圖以外（stage/scene3d 背景）固定黑色**，
  因此外徑鏈（edim，畫在圖外）恆用亮色不隨主題。**st=light 依賴白色預設按鈕 id=btnTheme，勿改 id**。

## 物件顏色

- 調色盤（#fColor input type=color，取代舊 16 色格）：選取物件即時套用、面板同步顯示 hex。

## 備註

- 物件 f.note（面板 #fNote textarea）與櫃體 f.cab.note（Modal #cabNote）皆為自由文字，
  隨存檔/匯出/複製；清單以 title 顯示、名稱後加 📝，3D 名稱標籤亦加 📝。hasCab 含 note。

## 系統內建物件（16 種＋人物）

- BUILTINS：桌子/冰箱/隔板60×30×2/床/沙發/鞋櫃/衣櫃/行李箱/登機箱/小椅子/
  小餐邊推車/垃圾桶/投影機/洗衣籃/**鞋子 24×10×9（腳長 24cm）**/**管柱 150×3.4×45**；
  同名尺寸取自 A2居家配置_0849.json，冰箱 json 值 20×60×195 不合理改用 60×70×180；
  **鞋櫃 2026-07-31 依使用者指定改 64×32×200**：內建於程式、不受存檔影響；
  **本質＝一般物件**（可自訂長寬高、受全部物件規則）；
  3D 以 SKIN3D 多部件外皮呈現（比例縮放）。**正面＝+y（預設視角近側）**：門面/櫃體開口/沙發座向皆同。
  **面板為統一下拉選單 #builtinSel＋「➕ 加入」**（含男/女主人 person:m|f，共 18 個 option，
  舊 #builtinGrid/btnMan/btnWoman 已移除）。

## 管柱（k=pipe）

- f.pipe='I'|'L'|'U'（面板 #fPipe，**預設 L 型**——markup option selected）＋管徑 f.pipeT（#fPipeT，
  預設 PIPE_T=3.4＝明管 25A 外徑；32A=4.3、PVC 電管=2；範圍 1~30，截面以方管近似圓管）；
  pipeParts(f) 推導部件——**直＝沿最長邊一根（w≥h 為水平貼頂、否則垂直）、L＝頂部橫段＋一端垂直段、
  U＝頂部橫段＋兩端垂直段**（依使用者提供的天花板轉折方管照片）；3D 走 SKIN3D.pipe、2D 俯視畫實際管段投影。
  **新增（addBuiltin）即釘天花板：o.z = CEIL − h**（如實景照片：管沿天花板走）；
  **預設色 #9aa3ad 金屬灰**（2026-07-31 改：舊深色 #3b3f45 在黑底 3D 幾乎隱形，使用者誤以為只有選取框）。
  **碰撞/磁吸仍用整體 OBB**（與所有既有物件規則一致）；固定方式＝臨邊支點：只要一端貼天花板或牆即釘住，
  兩端皆無支點才落地。

## 匯入換皮規則

- **匯入/載入存檔/還原版本時，名稱同內建物件者自動換皮（applySkins）——已有櫃體修改（hasCab）者除外**。
- **內建物件只要有櫃體修改儲存（closeCab 時 hasCab 為真）→ delete f.skin，外觀改為櫃體殼板**（2026-07-31
  改版，取代舊「SKIN_INNER 桌子保留外皮」機制——SKIN_INNER 已整個移除，所有物件進櫃體編輯一律殼板模型）。

## 上一步（復原）

- histStack（saveState→pushHistory 去重、上限 100）、Ctrl+Z 或 header「↩ 復原」；
  undo 以快照整批替換 furniture（**測試中 undo 後所有物件參照需 byId 重綁**）。
  **櫃體編輯 Modal 開啟中 pushHistory 凍結**：closeCab 後 refreshAll 記一步 → 主視圖「復原」＝整段櫃體
  編輯一步退回（外皮/cab 一起還原）。**Modal 內自有上一步 cabHist/cabPush/cabUndo**（↩ 上一步鈕；
  Ctrl+Z 於 Modal 開啟時路由至 cabUndo）；cabCommit()＝renderCab+syncCabPanel+refreshAll+cabPush，
  Modal 內所有完成操作走它。

## 選取懸浮功能列

- #selBar（單選時顯示於物件上方）：🗄 櫃體／⟳90°／⧉ 複製／🗑 刪除（人物無櫃體鈕）。

## 櫃體編輯 Modal

- （90vw×90vh）物件變空心殼（殼厚 CAB_TS=2cm、正面 +y 開放＝開口、無前板）＋隔板＋櫃內物品。
  f.cab={t(隔板厚度預設 2、範圍 0.4~3), parts:[{dir:'h'|'v',pos,t,color?,mat?}], items:[{w,d,h,x,y,z,skin?,...}],
  noBottom/noTop/noLeft/noRight/noBack, sc:{bottom/top/left/right/back:{color,mat}}}。
- **殼板五片（底/頂/左/右/背 CAB_BOARDS）與所有隔板皆為物件、皆可選取刪除**：3D 點選（點擊映射於
  內部空間之外＝選殼板、之內＝選放置格；endCabPtr 位移<5px 才算點擊）或側欄列表點選；刪除＝設 noX 旗標，
  恢復靠側欄 cabShellB/T/L/R/K 鈕；刪底板＝內底直接是地板（檯面下擺放）——內部座標原點＝內左緣/內底
  （cabInner 回傳 x0/z0/y0 偏移），切換殼板時物品/隔板座標平移補償、絕對位置不變（noBack 只改 idp 無補償）；
  hasCab 含旗標與 sc；closeCab 用 hasCab 判斷保留。
- **板材顏色/材質**：每片殼板（cab.sc[key]）與隔板（p.color/p.mat）可各自設定顏色＋特別材質——
  **玻璃 glass＝半透明 rgba 0.32（無自訂色時預設 #8ecae6）、洞洞板 peg＝radial-gradient 圓洞紋**
  （boardFill/cabShellFill；Modal、主視圖 3D、2D 俯視同步；CSS background 可含漸層層）。
- **放置物品可選內建物件**（#cabAddKind 下拉：自訂＋16 種；item 帶 skin 以外皮渲染於 Modal 與主 3D）；
  **尺寸一律取側欄輸入框當下值（#ciAddW/D/H＋#ciAddColor）**——選內建種類只是把其預設尺寸帶入輸入框
  （change 事件；測試若直接設 value 需自行 dispatch change），使用者可再改。
- **Modal 右上角工具列 #cabTools（位於 #cabView 內）：↩ 上一步／✔ 完成儲存（closeCab）／✕ 取消（cancelCab
  ＝回到 cabHist[0] 開啟當下狀態並關閉）**；**點擊 Modal 外不再關閉**（已移除背景 click 關閉，避免誤觸遺失編輯）；
  **Delete 鍵刪選取中的隔板**（其次殼板→物品）；**ESC＝完成儲存並關閉**；
  Modal 開啟時主視圖快捷鍵（R/方向鍵/Ctrl+C/V）一律不作用。櫃體備註 f.cab.note（#cabNote）。
- **放置物品新增規則（2026-07-31）**：須先點擊櫃內空白格選取「放置格」（cabCells＝隔板切出的網格、
  綠虛線高亮、cabSelCell 存 {xi,zi} 索引），且 cabCellCheck 過關（尺寸放得進格＋體積 ≤ 格剩餘體積＝
  格空間−已放物品體積和），否則拒絕新增；**放置決策 cabPlaceNewItem（自動判定水平或堆疊，4 層遞降）**：
  ①格內原為單層且加入後仍排得下→全部平均間隔並排（cabArrangeCell）；②否則**不動既有物品**、
  以「格底/各物品頂面」×「格左緣/各物品左右緣」為候選找最低最左可行位（cabAutoPlace，須真有支撐
  cabItemFloor 相符且 !cabItemBad；堆疊時支撐物體積須 ≥ 新物品＝大者在下）；③否則插入某一柱、
  該柱含新物品依體積降冪重堆（cabInsertColumn）；④否則整格重排；全部失敗才拒絕。
  **回歸重點：使用者手動拖曳堆疊後仍必須能繼續新增**（舊版只有「全並排/全單柱」兩種模式會誤擋）。
- 隔板新增自動延伸至內徑並平均分配（span*(i+1)/(n+1)＝由中間算起不貼邊）、可拖曳/輸入調位
  （clamp 僅限內徑範圍；**與同向隔板重疊＝整片變紅警示、放開退回**，v↔h 十字相交合法）；
  **移動水平隔板時其頂面上物品（含堆疊遞迴 cabItemsOn）連動位移**，物品壓到其他隔板也紅+退回。
- 物品規則特例：**下方必有支點（不會釘牆）**＝櫃底/隔板頂/其他物品頂（cabItemFloor＋cabSettleItems，
  掛在 settleGravity）；物品可互疊但總高不可超上方隔板（超過→cabItemBad 紅）；物品互相重疊＝紅。
  距離（cabItemDists）精準計入內徑、所有隔板厚度與其他物品；放不下（cabItemBad）整件變紅+放開退回。
- **懸停鄰近點規則（Modal 內，與主視圖 3D 統一＝六向：左右上下＋前後）**：懸停物品/隔板/櫃內任意
  空白點（cabPlaneFromScreen 反解深度中線平面）皆顯示鄰近距離（cabPointDists／cabItemDists 含
  front/back：開口側=前、背板側=後）。**主視圖 3D 懸停**：物品面標 data-ci → 顯示該物品六向距離標籤；
  懸停櫃體顯示內部空間（updateCabGuides，標籤文字＝「內部 W×D×H」）。
- cab 資料隨 furniture 存檔/匯出/複製；主 2D 顯內徑虛線框＋垂直隔板、主 3D 空心渲染（重疊隔板紅）。
  Modal 自有 3D（cabCam/cabPt 與 fwd3d 同構數學，供拖曳軸投影與懸停反解）。

## 多選／複製貼上

- Shift+點選多選＋R 群組旋轉（繞群組外框中心）；Ctrl+C/V 複製貼上；滾輪換疊放層。

## 平移（左+右鍵）

- **左+右鍵同時按住拖曳＝平移整張平面圖**（2D 移 viewBox、3D 移 cam.px/py，軸心/角度/縮放不變）：
  進行中的家具拖曳/旋轉即刻取消退回原位（abortActiveDrag）；右鍵單獨拖曳＝平移（2D/3D 一致）、
  右鍵不啟動家具拖曳、stage/scene3d 均 preventDefault contextmenu。

## 鍵盤微調

- **方向鍵微調選取物件 0.5cm/步**（nudgeSel）：直接位移不經磁吸（可突破磁鐵誤判），
  但不可覆蓋牆面/其他物件（違者整步阻擋+提示）；上方堆疊 pileAbove 連動；INPUT 聚焦或櫃體 Modal 開啟時不作用。

## 尺寸標註／3D 標籤

- 選取顯示長寬高：CAD 標註樣式畫在對應邊緣（2D 標註線、3D 邊緣 billboard）。
- 3D 標籤一律 billboard（反向抵銷 rotateX/rotateZ＋反縮放）。

## 教學 Modal

- 首次進站自動彈出（今日不再顯示存 localStorage 當日字串）、Header「❓ 教學」可重開；
  `?selftest=1` 時不自動彈出（st=tut 例外）。

## 版本管理

- 「💾 版本」：localStorage 多版本另存/還原/刪除（上限 30）；配置隨時自動儲存（重開機續編）。

## 高度上限＝天花板

- 新增即截斷；選取後右側輸入即時所見即所得套用（liveApply），
  改高度時堆疊上方物件隨頂面位移、整疊頂不可超過 CEIL（setHeight/pileAbove）。

## 流理台障礙

- 流理台（廚具）外框＝障礙物（walls 內 x354.53~414.53/y1010~1170 四段，由 add_counter_obstacle.py 加入）；
  洗手槽內框為純圖面、嚴禁進 WALLS。家具面板預設開啟。

## 門口（DOORS）

- 牆面共線群組 40~160cm 缺口自動推導（玄關大門 y1225/x130~230、主臥門、
  兩衛浴門、臥室中門）；懸停/拖曳家具時顯示「距門口 N」（OBB↔門段精確距離，4m 內、隨懸停清除）。

## 人物（kind='person'）

- 👨男主人 藍#2f6fd6 171cm/75kg、👩女主人 粉#f48fb1 154cm/48kg。
  可拖曳；永遠 z=0（不可離地）；不進磁吸/疊放；與任何物件/牆互為硬阻擋（dragBlocked）。
  3D 以身體＋頭部兩方塊呈現；清單與邊緣標籤顯示 身高/體重。
