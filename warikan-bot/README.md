# 割り勘Bot（walica連携）

企画チャンネルの参加者ロール保持者で、walica.jp の割り勘を作成する Discord Bot。

## セットアップ（VM上）

```bash
cd ~/discord-bots/warikan-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Playwright のブラウザ本体を導入（初回のみ）
playwright install chromium
# 依存ライブラリが足りない場合（Debian/Ubuntu）
playwright install-deps chromium

cp bot.env.example bot.env
nano bot.env   # トークンを記入
```

## walica操作の実装について

`walica.py` はフォーム構造が未確定のため土台のみ。
walica.jp/new の実際のセレクタが判明したら TODO 部分を実装すること。

## 起動（systemd）

サービス名 `warikan-bot` で event-starter と同様に登録する。
