# TikTok Daily Streak Bot

Automates sending a daily TikTok DM streak message using Selenium, GitHub Actions, and exported TikTok cookies.

> Original project by **TimeNitch**\
> Original template: `https://github.com/TimeNitch/Tiktok-Streak`

## Table of Contents

<details>
<summary>Setup & Security</summary>

- [Important Disclaimer](#important-disclaimer)
- [Features](#features)
- [Local Repository Structure](#local-repository-structure)
- [Security Warning](#security-warning)
- [Required GitHub Secrets](#required-github-secrets)
  - [Required](#required)
  - [Optional Discord Notification](#optional-discord-notification)
  - [Optional Telegram Notification](#optional-telegram-notification)

</details>

<details>
<summary>Installation</summary>

- [Installation: GitHub Actions](#installation-github-actions)
  - [1. Create your repository](#1-create-your-repository)
  - [2. Add GitHub Secrets](#2-add-github-secrets)
  - [3. Configure workflow schedule](#3-configure-workflow-schedule)
  - [4. Set workflow timeout](#4-set-workflow-timeout)
  - [5. Run manually for testing](#5-run-manually-for-testing)

</details>

<details>
<summary>Program Configuration</summary>

- [Program Configuration](#program-configuration)
  - [Debug Mode](#debug-mode)
  - [Message Text](#message-text)
  - [Target Time](#target-time)
  - [Wait Until Target Time](#wait-until-target-time)
  - [Precheck](#precheck)

</details>

<details>
<summary>Target Conversations</summary>

- [Choosing Target Conversations](#choosing-target-conversations)
  - [Desktop browser](#desktop-browser)
  - [Smartphone users](#smartphone-users)

</details>

<details>
<summary>Cookie Setup</summary>

- [Getting TikTok Cookies](#getting-tiktok-cookies)
- [Getting Cookies on Windows](#getting-cookies-on-windows)
  - [1. Install a browser extension](#1-install-a-browser-extension)
  - [2. Log in to TikTok](#2-log-in-to-tiktok)
  - [3. Open Cookie-Editor](#3-open-cookie-editor)
  - [4. Export cookies](#4-export-cookies)
  - [5. Add to GitHub Secret](#5-add-to-github-secret)
  - [6. Local testing on Windows](#6-local-testing-on-windows)
- [Getting Cookies on Android](#getting-cookies-on-android)
  - [1. Install Firefox](#1-install-firefox)
  - [2. Install Cookie-Editor](#2-install-cookie-editor)
  - [3. Log in to TikTok](#3-log-in-to-tiktok-1)
  - [4. Open Cookie-Editor](#4-open-cookie-editor)
  - [5. Export cookies](#5-export-cookies)
  - [6. Add to GitHub Secret](#6-add-to-github-secret)
- [Getting Cookies on iOS](#getting-cookies-on-ios)

</details>

<details>
<summary>Notifications</summary>

- [Discord Notification Setup](#discord-notification-setup)
  - [1. Create a Discord webhook](#1-create-a-discord-webhook)
  - [2. Add GitHub Secret](#2-add-github-secret)
  - [3. Local testing](#3-local-testing)
- [Telegram Notification Setup](#telegram-notification-setup)
  - [1. Create a Telegram bot](#1-create-a-telegram-bot)
  - [2. Start your bot](#2-start-your-bot)
  - [3. Find your chat ID](#3-find-your-chat-id)
  - [4. Add GitHub Secrets](#4-add-github-secrets)
  - [5. Local testing](#5-local-testing)
- [Notification Behavior](#notification-behavior)
  - [First precheck passed](#first-precheck-passed)
  - [Cookie problem / no target found](#cookie-problem--no-target-found)
  - [Debug Mode target collection](#debug-mode-target-collection)
  - [Messages sent successfully](#messages-sent-successfully)

</details>

<details>
<summary>Workflow, Testing & Troubleshooting</summary>

- [GitHub Actions Workflow Example](#github-actions-workflow-example)
- [Testing Checklist](#testing-checklist)
- [Common Problems](#common-problems)
  - [Cookie file not found](#cookie-file-not-found)
  - [Cookie file is empty](#cookie-file-is-empty)
  - [No target conversations found](#no-target-conversations-found)
  - [Discord notification returns 403 Forbidden](#discord-notification-returns-403-forbidden)
  - [GitHub Actions did not run exactly on time](#github-actions-did-not-run-exactly-on-time)

</details>

<details>
<summary>Credits & License</summary>

- [Credits](#credits)
- [License](#license)

</details>

## Important Disclaimer

This project is an automation template. Use it at your own risk.

TikTok may change its website, login system, cookie behavior, or anti-automation checks at any time. If that happens, the bot may stop working.

Do not use this project for spam, harassment, bulk messaging, or anything that violates TikTok rules or other people's privacy.

## Features

* Runs automatically using GitHub Actions.
* Uses TikTok cookies instead of logging in with a username/password.
* Supports scheduled sending at a target time, for example 08:00 Thailand time.
* Supports precheck before the target time to verify that cookies still work.
* Supports Discord and Telegram notifications.
* Saves logs and screenshots as GitHub Actions artifacts.
* Supports Debug Mode to collect targets without sending messages.

## Local Repository Structure

```text
.
├── .github/
│   └── workflows/
│       └── tiktok_streak_ubuntu.yml
├── Program.py
├── requirements.txt
├── README.md
├── .gitignore
├── cookie.txt
├── discord_webhook.txt
├── telegram_bot_token.txt
└── telegram_chat_id.txt
```

## Security Warning

Never commit real cookies, webhook URLs, Telegram bot tokens, screenshots, or log files.

Add these files to `.gitignore`:

```gitignore
cookie.txt
discord_webhook.txt
telegram_bot_token.txt
telegram_chat_id.txt
tiktok_bot.log
*.png
.idea
.venv
```

For GitHub Actions, store secrets in:

```text
Repository → Settings → Secrets and variables → Actions
```

## Required GitHub Secrets

### Required

```text
COOKIE
```

This contains your exported TikTok cookie data.

### Optional Discord Notification

```text
DISCORD_WEBHOOK_URL
```

### Optional Telegram Notification

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

You can use Discord only, Telegram only, both, or neither.

## Installation: GitHub Actions

### 1. Create your repository

Use this repository as a template, or copy the files into your own repository.

Recommended visibility:

* Public repo: GitHub-hosted standard Actions runners are generally free for public repositories.
* Private repo: GitHub Actions may use your monthly free minutes quota.

Even if the repo is public, your cookies and tokens are safe as long as you store them in GitHub Secrets and never commit them.

### 2. Add GitHub Secrets

Go to:

```text
Repository → Settings → Secrets and variables → Actions → New repository secret
```

Add:

```text
COOKIE
```

Optional:

```text
DISCORD_WEBHOOK_URL
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

### 3. Configure workflow schedule

GitHub cron uses UTC time.

Thailand time is UTC+7.

If you want the bot to send at **06:00 Thailand time** and start the workflow about 4 hours earlier, use:

```yaml
on:
  schedule:
    - cron: "0 19 * * *"
  workflow_dispatch:
```

Because:

```text
19:00 UTC = 02:00 Thailand time
```

Then set this inside `Program.py`:

```python
TARGET_RUN_TIME = "06:00:00"
WAIT_UNTIL_TARGET_TIME = 1
PRECHECK_BEFORE_WAIT = 1
```

If you want to send at **08:00 Thailand time** and start the workflow about 4 hours earlier, use:

```yaml
on:
  schedule:
    - cron: "0 21 * * *"
  workflow_dispatch:
```

Because:

```text
21:00 UTC = 04:00 Thailand time
```

Then set this inside `Program.py`:

```python
TARGET_RUN_TIME = "08:00:00"
WAIT_UNTIL_TARGET_TIME = 1
PRECHECK_BEFORE_WAIT = 1
```

### 4. Set workflow timeout

If the workflow starts several hours before the target time, increase `timeout-minutes`.

Recommended:

```yaml
timeout-minutes: 360
```

This is important. If the timeout is too short, GitHub Actions may stop the job before the bot sends the message.

### 5. Run manually for testing

Go to:

```text
Repository → Actions → TikTok Daily Streak (Ubuntu) → Run workflow
```

For safe testing, use Debug Mode first.

## Program Configuration

Open `Program.py` and edit the config section near the top.

### Debug Mode

```python
DEBUG_MODE = 1
```

Debug Mode means:

* Opens TikTok.
* Injects cookies.
* Collects target conversations.
* Sends notification if enabled.
* Does not send messages.

For real sending:

```python
DEBUG_MODE = 0
```

### Message Text

```python
MESSAGE_TEXT = os.getenv("TIKTOK_MESSAGE_TEXT", "Auto streak test 🔥")
```

You can change the default text directly or use the environment variable `TIKTOK_MESSAGE_TEXT`.

### Target Time

```python
TARGET_RUN_TIME = "08:00:00"
TARGET_TIMEZONE = timezone(timedelta(hours=7), name="Asia/Bangkok")
```

Supported formats:

```text
HH:MM
HH:MM:SS
```

Examples:

```python
TARGET_RUN_TIME = "06:00:00"
TARGET_RUN_TIME = "08:00:00"
TARGET_RUN_TIME = "17:30:15"
```

### Wait Until Target Time

```python
WAIT_UNTIL_TARGET_TIME = 1
```

If enabled, the program waits until `TARGET_RUN_TIME` before sending.

If disabled:

```python
WAIT_UNTIL_TARGET_TIME = 0
```

The program starts immediately and skips the precheck loop.

### Precheck

```python
PRECHECK_BEFORE_WAIT = 1
PRECHECK_INTERVAL_MINUTES = 10
PRECHECK_STOP_WITHIN_MINUTES = 5
```

Meaning:

* Run precheck every 10 minutes.
* Stop prechecking when target time is 5 minutes away or less.
* Then wait until the target time and send.

If precheck cannot find target conversations, the bot assumes the cookie may be invalid or logged out and aborts.

## Choosing Target Conversations

The bot sends messages only to conversations that are pinned on the TikTok messages page.

### Desktop browser

1. Open:

```text
https://www.tiktok.com/messages?lang=en
```

2. Log in to TikTok.
3. Pin the conversations that you want the bot to send messages to.
4. Run the bot in Debug Mode first to confirm that the pinned conversations are detected.

### Smartphone users

The TikTok mobile app may not work well for this setup because the app limits pinned conversations to around 5 conversations.

If you are using a smartphone, use the website instead:

1. Open your mobile browser.
2. Enable desktop site / desktop mode in the browser.
3. Open:

```text
https://www.tiktok.com/messages?lang=en
```

4. If TikTok redirects or shows the mobile view, enable desktop mode again and reload the link.
5. Pin the conversations that you want the bot to send messages to.
6. Run the bot in Debug Mode first to confirm that the pinned conversations are detected.

## Getting TikTok Cookies

The bot does not log in using your username and password. It uses exported cookies from a browser session.

The cookie must be from an already logged-in TikTok session.

## Getting Cookies on Windows

Recommended method: desktop browser + Cookie-Editor extension.

### 1. Install a browser extension

Install Cookie-Editor for Chrome, Edge, or Firefox.

### 2. Log in to TikTok

Open TikTok in the browser and log in normally.

Recommended URL:

```text
https://www.tiktok.com/messages?lang=en
```

Make sure you can see your messages.

### 3. Open Cookie-Editor

Click the Cookie-Editor extension icon while you are on TikTok.

### 4. Export cookies

Export cookies as JSON or text.

Copy the exported cookie data.

### 5. Add to GitHub Secret

Go to:

```text
Repository → Settings → Secrets and variables → Actions → New repository secret
```

Create:

```text
COOKIE
```

Paste the exported cookie data as the secret value.

### 6. Local testing on Windows

Create `cookie.txt` in the same folder as `Program.py`.

Paste the exported cookie data into `cookie.txt`.

Then run:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python Program.py
```

## Getting Cookies on Android

Recommended method: Firefox for Android + Cookie-Editor extension.

### 1. Install Firefox

Install Firefox from Google Play.

### 2. Install Cookie-Editor

Open Firefox and install the Cookie-Editor extension.

### 3. Log in to TikTok

Open:

```text
https://www.tiktok.com/messages?lang=en
```

Log in to TikTok.

Make sure the messages page loads.

### 4. Open Cookie-Editor

Open the Cookie-Editor extension while you are on TikTok.

### 5. Export cookies

Export the cookies.

Copy the exported data.

### 6. Add to GitHub Secret

Add the exported data to the `COOKIE` secret in GitHub.

## Getting Cookies on iOS

Current status: not recommended.

A Cookie-Editor app from the App Store may not be able to access Safari or TikTok browser cookies. In testing, after logging in to TikTok, the app reported that no cookies were found.

Because of that, iOS is not currently a reliable method for exporting TikTok cookies for this bot.

Recommended alternatives:

* Use Windows with a desktop browser.
* Use Android with Firefox and Cookie-Editor.
* Use another desktop browser that supports cookie export extensions.

## Discord Notification Setup

### 1. Create a Discord webhook

In Discord:

```text
Server Settings → Integrations → Webhooks → New Webhook
```

Choose the channel and copy the webhook URL.

### 2. Add GitHub Secret

Create this repository secret:

```text
DISCORD_WEBHOOK_URL
```

Paste the webhook URL.

### 3. Local testing

For local testing, create:

```text
discord_webhook.txt
```

Paste only the webhook URL inside the file.

Do not commit this file.

## Telegram Notification Setup

Telegram notification needs two values:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

### 1. Create a Telegram bot

Open Telegram and search for:

```text
@BotFather
```

Send:

```text
/newbot
```

Follow the instructions.

BotFather will give you a bot token.

### 2. Start your bot

Open your new bot in Telegram and press:

```text
Start
```

Send any message to the bot, for example:

```text
test
```

### 3. Find your chat ID

Open this URL in a browser:

```text
https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
```

Find:

```json
"chat": {
  "id": 123456789
}
```

That number is your `TELEGRAM_CHAT_ID`.

### 4. Add GitHub Secrets

Create:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

### 5. Local testing

For local testing, create:

```text
telegram_bot_token.txt
telegram_chat_id.txt
```

Do not commit these files.

## Notification Behavior

The bot sends notifications in these cases:

### First precheck passed

The first precheck was successful and target conversations were found.

### Cookie problem / no target found

The bot could not find any target conversations. This usually means the cookie is invalid, expired, logged out, or TikTok did not load messages correctly.

A screenshot is attached if available.

### Debug Mode target collection

If `DEBUG_MODE = 1`, the bot sends a notification showing collected target names and skips message sending.

### Messages sent successfully

If `DEBUG_MODE = 0`, the bot sends a notification after all messages are sent.

## GitHub Actions Workflow Example

```yaml
name: TikTok Daily Streak (Ubuntu)

on:
  schedule:
    - cron: "0 21 * * *"
  workflow_dispatch:

jobs:
  run-bot:
    runs-on: ubuntu-latest
    timeout-minutes: 360

    steps:
      - name: Checkout repository code
        uses: actions/checkout@v4

      - name: Create secret files
        env:
          COOKIE_DATA: ${{ secrets.COOKIE }}
          DISCORD_WEBHOOK_DATA: ${{ secrets.DISCORD_WEBHOOK_URL }}
          TELEGRAM_BOT_TOKEN_DATA: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID_DATA: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: |
          cd "$GITHUB_WORKSPACE"
          python3 - <<'PY'
          import os
          from pathlib import Path

          def write_required_secret(env_name, file_name):
              value = os.environ.get(env_name, "")
              if not value.strip():
                  raise SystemExit(f"{env_name} secret is empty or missing")
              Path(file_name).write_text(value.strip(), encoding="utf-8")
              print(f"{file_name} created")
              print(f"{file_name} length:", len(value.strip()))

          def write_optional_secret(env_name, file_name):
              value = os.environ.get(env_name, "")
              if value.strip():
                  Path(file_name).write_text(value.strip(), encoding="utf-8")
                  print(f"{file_name} created")
                  print(f"{file_name} length:", len(value.strip()))
              else:
                  print(f"{env_name} is empty or missing; skipped {file_name}")

          write_required_secret("COOKIE_DATA", "cookie.txt")
          write_optional_secret("DISCORD_WEBHOOK_DATA", "discord_webhook.txt")
          write_optional_secret("TELEGRAM_BOT_TOKEN_DATA", "telegram_bot_token.txt")
          write_optional_secret("TELEGRAM_CHAT_ID_DATA", "telegram_chat_id.txt")
          PY

      - name: Create and Install Python virtual environment
        run: |
          cd "$GITHUB_WORKSPACE"
          python3 -m venv venv
          source venv/bin/activate
          pip install -r requirements.txt

      - name: Run TikTok Bot Script
        run: |
          cd "$GITHUB_WORKSPACE"
          source venv/bin/activate
          python Program.py

      - name: Upload debug artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: tiktok-debug-artifacts
          path: |
            *.log
            *.png
```

## Testing Checklist

Before using real sending mode:

* Set `DEBUG_MODE = 1`.
* Run workflow manually.
* Confirm the bot can collect target conversations.
* Confirm Discord or Telegram notification works.
* Confirm screenshots and logs are uploaded as artifacts.
* Then set `DEBUG_MODE = 0` for real sending.

## Common Problems

### Cookie file not found

The `COOKIE` secret may be missing, or `cookie.txt` was not created.

### Cookie file is empty

The `COOKIE` secret exists but has no value.

### No target conversations found

Possible causes:

* Cookie expired.
* TikTok session logged out.
* TikTok messages page did not load.
* TikTok changed the conversation item HTML.
* Account has no matching target conversations loaded.

### Discord notification returns 403 Forbidden

Discord may require a non-default User-Agent header. This project already sends a browser-like User-Agent for Discord requests.

If it still fails:

* Regenerate the Discord webhook.
* Make sure the webhook URL is complete.
* Make sure the webhook still exists.
* Make sure the channel still allows webhook messages.

### GitHub Actions did not run exactly on time

GitHub scheduled workflows can be delayed. This project works around that by starting the workflow earlier and letting `Program.py` wait until the target time.

## Credits

Original project by **TimeNitch**.

If you use this template, please keep attribution in your README, LICENSE, or project documentation.

## License

Recommended license: Apache-2.0 or MIT.

If you want stronger attribution, use Apache-2.0 with a `NOTICE` file.
