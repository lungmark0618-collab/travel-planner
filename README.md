# ✈️ 智慧旅遊規劃師

一個手機優先設計的旅遊規劃與記帳 App，使用 Streamlit 建置。

## 功能

- 📅 **行程規劃** — 新增、編輯、刪除每日行程
- 💰 **記帳本** — 支援 JPY、TWD、USD、EUR、KRW 多幣別自動換算
- 📊 **總覽看板** — 視覺化花費分析（圓餅圖 + 長條圖）
- ⚙️ **旅程設定** — 自訂旅程名稱、預算、匯率（支援一鍵即時匯率）

## 本地啟動

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 部署到 Streamlit Cloud

1. 將此資料夾上傳到 GitHub
2. 前往 [share.streamlit.io](https://share.streamlit.io)
3. 連結 GitHub repo，選擇 `app.py` 作為主程式
4. 點擊 Deploy！

## 資料儲存說明

> **注意：** Streamlit Cloud 的免費版是無狀態的，每次 redeploy 都會清除 `travel_data.json`。
> 建議使用 **Streamlit Community Cloud** 的 Secrets 或外部資料庫（如 Supabase）來持久化資料。
> 本地端使用則完全正常，資料儲存在同目錄的 `travel_data.json`。
