# Android E2E Automation Solution

## Goal

Automate an Android E2E flow:

1. Connect to a remote Android device through Appium.
2. Check Google Play login state.
3. Log in only when required.
4. Install Brawl Stars from Google Play if it is not installed.
5. Launch the game.
6. Handle onboarding screens.
7. Detect whether the game is already in the main menu.
8. Navigate to the shop.
9. Perform a payment dry-run by detecting the offer/payment entry point.
10. Finish within a 180-second execution budget.

## Runtime

The script is designed to run from Replit as an orchestration layer.

Replit stores:
- Python code
- environment variables
- device provider credentials
- execution logs

The Android device itself is provided by a remote device-farm provider through an Appium endpoint.

## Required Environment Variables

```env
GOOGLE_EMAIL=
GOOGLE_PASSWORD=
APPIUM_SERVER=
DEVICE_UDID=
```

## Automation Stack

Python
Appium
UiAutomator2
OpenCV template matching
Android shell input
dotenv
Remote Android device provider

## Replit Usage

Replit is used as a lightweight orchestration environment for running the Python automation script.

It is responsible for:

- Storing and running the Python code.
- Managing environment variables through Replit Secrets.
- Connecting to a remote Appium server through `APPIUM_SERVER`.
- Passing the target Android device id through `DEVICE_UDID`.
- Collecting console logs and debug screenshots.

The Android device itself is not expected to run inside Replit.

Instead, the device is provided by one of the following options:

- A remote real-device provider.
- A private Android device farm.
- A cloud Android emulator with an exposed Appium endpoint.
- A local machine running Appium, exposed to Replit through a tunnel.

In this setup, Replit acts only as the control plane, while Appium and the Android device act as the execution environment.

## Execution Architecture

```text
Replit
  |
  | Python + Appium client
  v
Remote Appium Server
  |
  | UiAutomator2
  v
Android Device / Emulator
  |
  v
Google Play + Brawl Stars
```

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

DOM Resilience
The script does not rely only on DOM selectors.

For important actions it uses a hybrid approach:
1. Try XPath / UiAutomator selector.
2. If DOM changes or selector fails, fallback to OpenCV template matching.
3. If CV also fails, save a debug screenshot and use a controlled fallback when safe.

## CV Templates

Require: 
```assets/google_signin_btn.png
assets/install_btn.png
assets/age_slider.png
assets/level0_start.png
assets/shop_btn.png
assets/name_ok_btn.png
assets/offer_price.png
```

## Payment Safety

The script performs only a payment dry-run.
It reaches the offer/payment entry point and validates that the purchase flow can be opened.
Final purchase confirmation is not automated outside an authorized billing test environment.

## Timing Notes

The target execution time is up to 180 seconds for a warm-device scenario:

- Google Play is already logged in or the login session is cached.
- The game is already installed or installs quickly.
- The game assets are already cached.
- The first launch does not require long additional downloads.

A cold start with fresh Google login, full Play Store installation, or long in-game asset loading may exceed 180 seconds because these steps depend on Google Play, network speed, device performance, and game-side loading time.
