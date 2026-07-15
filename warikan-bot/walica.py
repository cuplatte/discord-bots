"""
walica.jp 操作モジュール（Playwright）
--------------------------------------
walica.jp/new を開き、タイトルとメンバーを入力して割り勘を作成し、
作成された割り勘ページのURL（末尾の /share を除いたもの）を返す。

フォーム構造（2026-07 時点）:
  - タイトル: placeholder="北海道旅行" の text input
  - メンバー: #member-input に入力 → 「追加」ボタン押下を人数分繰り返す
  - 作成:     「グループを作成」ボタン
  - 作成後:   URL 末尾の /share を除いたものが割り勘ページ

注意:
  walica はSPA（JavaScriptでフォームを描画）のため、goto直後は要素が無い。
  各要素は wait_for で出現を待ってから操作する。
"""

import os
import asyncio
from playwright.async_api import async_playwright

WALICA_NEW_URL = "https://walica.jp/new"
HEADLESS = os.environ.get("WALICA_HEADLESS", "1") == "1"

# セレクタ定義（構造が変わったらここを直す）
SEL_TITLE = 'input[placeholder="北海道旅行"]'
SEL_MEMBER_INPUT = "#member-input"
SEL_ADD_BUTTON = 'button:has-text("追加")'
SEL_CREATE_BUTTON = 'button:has-text("グループを作成")'

# 要素待ちのタイムアウト（ミリ秒）
WAIT_TIMEOUT = 20000


async def create_walica_project(title: str, member_names: list) -> str:
    """
    walica.jp に割り勘を作成し、作成ページのURLを返す。

    Args:
        title: 割り勘のタイトル（チャンネル名）
        member_names: 参加者の表示名リスト

    Returns:
        作成された割り勘ページのURL（末尾の /share を除去済み）
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        try:
            page = await browser.new_page()
            await page.goto(WALICA_NEW_URL, wait_until="domcontentloaded")

            # --- (1) タイトル欄の出現を待ってから入力 ---
            # SPAなので描画されるまで待つ
            title_input = page.locator(SEL_TITLE)
            await title_input.wait_for(state="visible", timeout=WAIT_TIMEOUT)
            await title_input.fill(title)

            # --- (2) メンバーを1人ずつ入力して「追加」を押す ---
            member_input = page.locator(SEL_MEMBER_INPUT)
            await member_input.wait_for(state="visible", timeout=WAIT_TIMEOUT)

            for name in member_names:
                await member_input.fill(name)

                # 入力すると「追加」ボタンの disabled が外れる想定。
                # 有効化を待ってから押す。
                await page.wait_for_function(
                    """() => {
                        const btns = [...document.querySelectorAll('button')];
                        const b = btns.find(el => el.textContent.includes('追加'));
                        return b && !b.disabled;
                    }""",
                    timeout=WAIT_TIMEOUT,
                )
                await page.locator(SEL_ADD_BUTTON).click()

                # 追加処理と入力欄クリアを待つ
                await page.wait_for_timeout(400)

            # --- (3) 「グループを作成」ボタンの有効化を待って押す ---
            await page.wait_for_function(
                """() => {
                    const btns = [...document.querySelectorAll('button')];
                    const b = btns.find(el => el.textContent.includes('グループを作成'));
                    return b && !b.disabled;
                }""",
                timeout=WAIT_TIMEOUT,
            )

            # 押下後、/share へのURL遷移を待つ。
            # walicaはクライアントサイドルーティングでURLを変えているらしく、
            # expect_navigation（フレームナビゲーションイベント依存）では遷移を検知できない。
            # そのためURLそのものをポーリングする wait_for_url を使う。
            await page.locator(SEL_CREATE_BUTTON).click()
            await page.wait_for_url("**/share*", timeout=WAIT_TIMEOUT)

            # --- (4) 遷移後URLから末尾の /share を除去 ---
            final_url = page.url
            if final_url.endswith("/share"):
                final_url = final_url[: -len("/share")]
            else:
                final_url = final_url.replace("/share", "")

            return final_url

        finally:
            await browser.close()


# --- 単体テスト用（VM上で python walica.py で動作確認できる）---------------
if __name__ == "__main__":
    async def _test():
        url = await create_walica_project("テスト旅行", ["あおい", "ゆうと", "はると"])
        print("作成されたURL:", url)

    asyncio.run(_test())
