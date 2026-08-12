# User Guide

## Logging in

Enter the email/password of your EchoDesk account — the same one your
devices are registered under (via the Agent's enrollment). Check
"Remember me" to stay logged in between launches (your refresh token is
stored encrypted using Windows' own credential protection — nothing is
ever stored in plain text).

## Dashboard

At a glance: total/online/offline device counts, your 10 most recent
commands, and your 10 most recent activity events. Refreshes automatically
(default every 30 seconds — adjustable in Settings).

## Devices

Every device on your account, as a card showing name, OS, hostname, last
seen, and current CPU/RAM/Disk/Battery. Search by name or hostname, sort by
name/status/last-seen, and switch between Grid and List layouts. Click any
device to open Device Details.

## Device Details

Full system/network/hardware info plus live-updating CPU and RAM history
charts (points arrive as the device's next heartbeat comes in — this app
polls, it doesn't get instant push updates; see the README's "known
limitations"). Delete Device permanently removes it from your account.

## File Manager

Pick a device, then:
- **Download File** — enter the exact remote path, click Download. Once
  the command's status becomes "Success" in the history table below,
  click **Save As...** to pick where to save it locally.
- **Upload File** — choose a local file, enter the destination path on the
  device, click Upload.
- **Delete File** — enter the exact remote path, confirm, click Delete.
- **Request Listing** is available but its result can't currently be
  shown — see the note on the page itself and the README for why. You'll
  need to already know the exact path for the three operations above.

## Command Center

Pick a device, then:
- **Quick Actions** — one click for Lock/Restart/Shutdown/Sleep/
  Hibernate/Log Out/Screenshot. Destructive ones (Shutdown/Restart/Log
  Out/Hibernate) ask for confirmation first.
- **Send Message** — shows a message on the device's screen.
- **Command History** — every command you've sent, with live status.
  Screenshots and file downloads get a **View / Save...** button once
  they succeed.

## Activity Logs

A record of account events (logins, password changes, etc.) — search,
filter by category, and export to CSV.

## Notifications

Wired to your account's notifications. Currently always empty — the
backend doesn't yet generate device-online/offline or command-result
notifications. This page will populate automatically the moment it does,
with no update needed to this app.

## Settings

Backend URL, TLS verification, poll intervals, default "Remember me"
state, and theme. Changes take effect after restarting the app.

## Profile

View your account email/name, change your password, and log out.
