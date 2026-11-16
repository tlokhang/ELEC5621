# 課程要求復查（2026-11-14）

依據：ELEC5621_Project.pdf 第 1–4 頁及工作區現有程式與輸出。結論：頭頸偏航穩定原型已完成，整份課程項目尚未完成。原 task_plan 的 complete 僅適用於原型階段。

| PDF 要求 | 現有證據 | 判定與缺口 |
| --- | --- | --- |
| p1–2：至少一個階段或關鍵功能 | 世界座標視線偏航穩定 | 部分符合；可作 Attention and Response 的關鍵子功能，但尚缺明確情境及功能映射 |
| p1–2：穩定等待、使用者 cue、指定目標 | mocap 固定軀幹，0.5 s 後開始擺動；視線目標是初始方向 | 部分符合；cue 只觸發擾動，沒有 cue 後轉向目標；固定支架不證明雙足平衡 |
| p2：生物機制、相關機器人研究、方法比較及設計依據 | 官方模型來源與控制公式已記錄 | 未完成；缺有引用的生物機制與相關研究綜述，不能只因題目叫「雞頭」便宣稱仿生依據充分 |
| p2：設計規格、自由度、感測、控制、運作條件、量化準則 | 四個頭頸關節；實際控制偏航；使用理想狀態；有振幅頻率及 RMS | 部分符合；需完整規格和事先定義的成功門檻、目標到達/穩定時間與適用範圍 |
| p3：模擬或實體概念驗證、允許規則/回授 | MuJoCo、三種控制器、官方資產來源及修改 | 原型符合；GPU、RL、實體機器人均非必需 |
| p3：明確條件與 baseline | 相同軀幹輸入下三控制器、九組振幅頻率 | 已具備偏航子系統比較 |
| p3：重複試驗及量化結果 | 九個不同條件，各控制器各一次；本次重跑通過 | 部分符合；掃描不是每條件多次試驗。需明列重複次數、結果離散程度；PDF 未強制隨機化，若用隨機試驗應記錄 seed |
| p3：討論限制與改進 | 已記錄理想感測、無雙足平衡、mocap 動力學限制 | 已具備原型討論；不能推論完整三維雞頭穩定或慣性抗擾 |
| p3–4：不超過 10 頁 PDF 報告 | 只有開發 Markdown | 未完成 |
| p3–4：15 分鐘演示、PowerPoint、錄影或現場展示 | 只有離線 CSV/JSON/誤差曲線 | 未完成；尚無選定行為的可視化演示流程或影片 |
| p4：組員貢獻百分比、提交 | 工作區無資料 | 未核實；不得代填組員貢獻或聲稱已提交 |

## 範圍解讀

PDF p2 允許只驗證一個階段或關鍵功能，p3 允許深化關鍵組件。因此並非硬性要求四個階段、走路、完整三維控制或獨立研發全身控制器。頭頸支架可作子系統概念驗證，但報告必須解釋其在穩定陪伴機器人中的作用、支撐假設和未驗證項。若聲稱完成機器人的 Attention and Response，就仍缺 cue-to-target 與保持平衡的證據。課程對支架子系統範圍的最終認可不能由現有測試保證。

## 本次驗證

執行 `.venv/bin/python scripts/verify_head_stabilization.py` 成功。九組條件下 optimized 均優於原補償，偏航關節未超限；CSV 抽樣不影響指標，五個非法參數測試通過。RMS 範圍 0.498–4.446°。這不能證明全部關節、全身穩定、噪聲/延遲或統計可靠性。

另有 Matplotlib Axes3D 匯入警告，現有二維圖表不受影響；尚未驗證三維展示環境。程式以步末時間標示 cue，但命令使用步初時間，cue 邊界可能相差一個 2 ms 步長；若加入反應時間評估，應先統一定義。

## 優先補齊

1. 明確選定「訊號後轉向目標並穩定視線」與成功準則，落實目標變更和可視化展示。
2. 在整體設計中處理穩定等待/平衡；明確區分支架驗證與全身驗證。
3. 補文獻與生物機制到控制設計的對應，安排重複試驗並完整記錄。
4. 製作不超過 10 頁 PDF、PowerPoint、錄影或可現場演示的程序及真實組員分工。

PDF 記載：2026-11-26 23:59 前在 Canvas 提交 PDF 及 PowerPoint；2026-11-27 作 15 分鐘報告及簡短問答。本次未查看 Canvas，也未提交任何檔案。

## 後續更新：2026-11-14
已實作 cue-to-target 與 12 組有 seed 的配對重複試驗，見 ATTENTION_RESPONSE.md 及 results/attention_response/summary.json。上表的目標轉向及重複試驗缺口已有子系統層面的證據；穩定等待/全身平衡、文獻與正式提交物仍未完成。

## 2026-11-14 Whole-body and report extension
Added free-base standing controller (bias compensation, damping and ankle/hip attitude feedback), 12 paired 10 s trials with target cues and small pushes. Balanced 12/12, baseline 0/12; peak tilt 14.03 deg, no non-foot contacts or joint-limit violations beyond 0.01 rad tolerance. This is bounded standing evidence, not comprehensive robustness. Added cited literature and formal English report PDF with source/builder. Member identities/contributions remain unfilled; slides and full-robot video remain pending. See FULL_BODY_BALANCE.md.
