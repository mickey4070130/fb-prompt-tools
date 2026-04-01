# FB Prompt Tool

手機優先的文案工具網站。現在包含：
- 主頁：`index.html`
- FB Prompt 工具頁：`fb-post.html`

## 本機預覽
在專案目錄執行：

```bash
python -m http.server 8000
```

打開：
- `http://localhost:8000`

---

## GitHub Pages 自動部署（免費）
此專案已包含 workflow：`.github/workflows/deploy-pages.yml`

### 第一次設定
1. 建立 GitHub Repository（例如：`fb-prompt-tools`）
2. 把此專案 push 到 `main` 分支
3. 到 GitHub 專案頁面：`Settings -> Pages`
4. 在 `Build and deployment` 選 `Source: GitHub Actions`
5. 等待 Actions 跑完（約 1~2 分鐘）

完成後網址會是：
- `https://<你的帳號>.github.io/<repo-name>/`

### 之後更新
只要 push 到 `main`，網站就會自動重新部署。

