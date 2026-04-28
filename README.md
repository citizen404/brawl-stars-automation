# Brawl Stars Automation (Google Play → Game → Payment Flow)

This project implements an end-to-end mobile automation scenario:

- Log into a Google account (pre-configured session)
- Install and launch Brawl Stars
- Pass onboarding
- Complete the tutorial level
- Navigate to in-game purchase
- Open Google Pay (dry run)

---

## ⚠️ Important Note

Automation is executed **outside of Replit**, on a machine with:
- Android emulator
- Appium
- Local agent

Replit is used only as a **control layer (API)**.

---

# 🧩 System Design

The system is divided into two logical layers:

## 1. Execution Layer (Device-side)

Runs on a local machine or device farm.

Components:
- Android Emulator (MuMu / Android SDK)
- Appium (UI automation driver)
- `main.py` (automation сценарий)

Responsibilities:
- Control the device UI
- Execute the full scenario
- Handle dynamic UI and game logic

---

## 2. Control Layer (Remote API)

Runs on Replit.

Components:
- FastAPI server (`server.py`)
- HTTP API (`/run`)

Responsibilities:
- Trigger automation remotely
- Act as a centralized controller
- Enable scaling to multiple devices

---

# 🔗 Communication

Replit cannot access local devices directly.

To solve this:

- A lightweight **agent** runs on the device machine
- **ngrok** exposes the agent to the internet

---

## Flow 
```
Replit → HTTP → ngrok → agent → main.py → Appium → device
```
---

# ⚙️ Components Explained

## Appium

Appium is used as a **device driver**.

It allows:
- tapping elements
- swiping
- entering text
- interacting with UI via locators

It replaces raw ADB commands with a higher-level abstraction.

---

## Agent (`infra/agent.py`)

A lightweight FastAPI server running locally.

Responsibilities:
- expose `/run` endpoint
- start `main.py` via subprocess

---

## ngrok

A tunneling service that exposes the local agent to the internet.

Without ngrok:
- Replit cannot reach the device

---

## Replit (`infra/server.py`)

Acts as a **control plane**.

Responsibilities:
- expose `/run` API
- forward requests to agent
- orchestrate execution

---

## Execution Architecture

```text
Replit (Control Layer API)
  |
  | HTTP
  v
Ngrok (tunnel)
  |
  | POST /run
  v
Agent (server)
  |
  | subprocess
  v
main.py
  |
  | commands
  v
Appium
  |
  | UI Control (UiAutomator2)
  ↓
Emulator → Game → Google Pay (dry run)
```
1. User sends request:
POST /run
2. Replit forwards request to agent via ngrok
3. Agent runs: python main.py
4. `main.py`:
- opens Play Store
- installs Brawl Stars
- completes onboarding
- passes tutorial level
- opens purchase screen
- detects Google Pay

## Device Provider Requirements

The remote device provider must support:
Android real devices or stable Android emulators
Remote Appium endpoint
Device allocation through API
Persistent device state
App installation from Google Play
Screenshot capture
Appium logs
Session timeout control
Device release through API

## Possible providers:

AWS Device Farm
BrowserStack App Automate
Sauce Labs Real Device Cloud
HeadSpin
Private Appium Grid

---

# 💳 Payment (Dry Run)

The script does NOT complete payment.

Instead it:
- opens Google Pay UI
- verifies it is displayed
- stops execution

---

# 🧠 Robustness

The system handles unstable UI using:

- multiple locator strategies
- fallback interactions
- state-based loops (instead of fixed steps)
- random gameplay to avoid idle detection

---

# 🤖 CV / UI Adaptation
CV is used as a fallback mechanism when UI elements are not accessible
via standard locators (e.g., game canvas or dynamic UI).

Basic visual fallback is implemented for cases where:
- UI elements are not accessible via DOM
- game uses canvas-based rendering

---

# 🏗️ Why This Architecture?

Direct execution from Replit is not possible because:

- Replit has no access to local devices
- Appium requires a real device/emulator

Therefore:

- Execution is moved to a local node (agent)
- Control is handled remotely via API
- ngrok bridges the network gap

This architecture allows connecting multiple agents, enabling a simple device farm.

---

# 🔌 How to Run

## On execution machine:

```bash
appium
uvicorn infra.agent:app --host 0.0.0.0 --port 9000
ngrok http 9000
```

In Replit
```bash
uvicorn infra.server:app --host 0.0.0.0 --port 3000
```
Trigger Scenario
```bash
curl -X POST https://your-replit-url/run
```
---

## Timing Notes

The target execution time is up to 180 seconds for a warm-device scenario:

- Google Play is already logged in or the login session is cached.
- The game is already installed or installs quickly.
- The game assets are already cached.
- The first launch does not require long additional downloads.

A cold start with fresh Google login, full Play Store installation, or long in-game asset loading may exceed 180 seconds because these steps depend on Google Play, network speed, device performance, and game-side loading time.

---

🧾 Summary

This project implements a distributed mobile automation system:

Execution is performed on devices via Appium
Control is handled via API (Replit)
Communication is enabled through agent + ngrok

The system is resilient, scalable, and aligned with the requirements.
