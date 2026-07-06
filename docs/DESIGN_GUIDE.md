# DESIGN_GUIDE.md
# YT Music Downloader — Visual and UX Design Specification

Author : Biraj Sarkar  
Version: 1.0

This document defines every visual, layout, and interaction detail.
The approved mockup (Windows landscape, Educative Scraper style) is the
reference. Nothing here is aspirational — every item is required.

---

## 1. Visual Language

**Style:** Windows-native, light theme. Not web-style, not dark, not flat-
minimal dark like a consumer app. It should look like a tool — similar to
the Educative Scraper reference image the user provided: structured, dense
but not cramped, Segoe UI, standard Windows controls.

**Palette — all hardcoded, no CSS variables:**

| Token            | Value       | Used for                                    |
|------------------|-------------|---------------------------------------------|
| `BG_WINDOW`      | `#F0F0F0`   | Main window / dialog background             |
| `BG_INPUT`       | `#FFFFFF`   | Text inputs, list backgrounds               |
| `BG_GROUPBOX`    | `#FAFAFA`   | Groupbox fill                               |
| `BG_BUTTON`      | `#E8E8E8`   | Standard buttons                            |
| `BG_BUTTON_HOV`  | `#D8D8D8`   | Button hover                                |
| `BG_TAB_ACTIVE`  | `#F0F0F0`   | Active tab (same as window; merges visually)|
| `BG_TAB_IDLE`    | `#C8C8C8`   | Inactive tabs                               |
| `BG_TITLEBAR`    | `#2D5FA8`   | Title bar background                        |
| `ACCENT`         | `#2980B9`   | Progress bars, active mode button           |
| `ACCENT_LIGHT`   | `#DAE8F8`   | Active mode button background               |
| `ACCENT_BORDER`  | `#4A90D9`   | Active mode button border                   |
| `TEXT_PRIMARY`   | `#111111`   | All main text                               |
| `TEXT_SECONDARY` | `#555555`   | Sublabels, hints, metadata rows             |
| `TEXT_DISABLED`  | `#AAAAAA`   | Disabled controls                           |
| `TEXT_TITLEBAR`  | `#FFFFFF`   | Title bar text                              |
| `GREEN`          | `#27AE60`   | Done state, success icons                   |
| `GREEN_LIGHT`    | `#D4EDDA`   | "Up to date" pill background                |
| `GREEN_DARK`     | `#155724`   | "Up to date" pill text                      |
| `RED`            | `#C0392B`   | Error state, validation errors              |
| `RED_LIGHT`      | `#FDE8E8`   | Error panel background                      |
| `AMBER`          | `#E67E22`   | Paused / update-available state             |
| `AMBER_LIGHT`    | `#FFF3CD`   | "Update available" pill background          |
| `AMBER_DARK`     | `#856404`   | "Update available" pill text                |
| `BLUE_LIGHT`     | `#CCE5FF`   | "Updating" pill background                  |
| `BLUE_DARK`      | `#004085`   | "Updating" pill text                        |
| `BORDER`         | `#AAAAAA`   | Input and groupbox borders                  |
| `BORDER_LIGHT`   | `#DDDDDD`   | Internal dividers, queue row borders        |

**Font:** `Segoe UI`, 12 px default, 13 px section labels, 11 px sublabels
and hints. Set via `QApplication.setFont(QFont("Segoe UI", 9))` (Qt uses
points; 9 pt ≈ 12 px at 96 DPI).

**Qt Style:** `QApplication.setStyle(QStyleFactory.create("Fusion"))`. This
gives consistent rendering across Windows 10 and Windows 11 without depending
on the system's visual style engine.

---

## 2. Window

**Default size:** 700 × 540 px.  
**Minimum size:** 600 × 460 px.  
**Resizable:** yes.  
**Position:** restored from `config.json` on launch. If off-screen (monitor
layout changed), recentre on primary screen.  
**Window title:** "YT Music Downloader" normally. During active download:
"YT Music Downloader — Downloading... 47%". After completion: reverts.  
**Window icon:** music note icon (`.ico` file). Placeholder acceptable for v1.

---

## 3. Title Bar

Custom title bar rendered via `QMainWindow` styling, NOT the system title bar.

Layout (left to right):
- Music note icon, 14 px
- "YT Music Downloader" — white, Segoe UI, 13 px
- Right side: minimise `—`, maximise `□`, close `✕` — each 22×22 px,
  white text, hover background rgba(255,255,255,0.2), close hover #C42B1C

Background: `#2D5FA8`.

---

## 4. Tab Strip

Sits immediately below the title bar.

- Background: `#DCDCDC`
- Border-bottom: 1 px `#AAAAAA`
- Padding: 6 px left, 8 px top-pad before tabs, 0 bottom
- Tabs: Downloader | Settings | About

Each tab:
- Padding: 5 px top, 16 px horizontal
- Border: 1 px solid on left/top/right; none on bottom
- Border-radius: 3 px top-left, 3 px top-right
- Inactive: background `#C8C8C8`, text `#444444`
- Hover: `#D8D8D8`
- Active: background `#F0F0F0` (same as window); border `#AAAAAA`;
  border-bottom-color matches window background (tab merges into body);
  text `#000000`, font-weight 500

Only one tab active at a time. Switching tabs is instant; no loading state.

---

## 5. Downloader Tab

### 5.1 Layout

Fixed-label form layout. Labels are right-aligned, width 120 px, text
`#333333`, 12 px. Controls sit to the right. Padding: 14 px all sides.
Row gap: 10 px.

### 5.2 Mode row

Label: "Mode:"  
Two equal-width buttons side by side, gap 6 px, height 28 px.

Button states:
- Inactive: background `#E8E8E8`, border 1 px `#888888`, text `#333333`
- Active: background `#DAE8F8`, border 1 px `#4A90D9`, text `#1A5A9C`,
  font-weight 500
- Each button has a small icon left of the text:
  - New download: `ti-download` (Tabler icon), 13 px
  - Update playlist: `ti-refresh`, 13 px

Only one mode active at a time. Mode applies to the next item added.
The selected mode is shown as a small tag on each queue row
("New" or "Update") so mixed-mode queues are legible.

### 5.3 URL input row

Label: "URL:"  
Text input: flex-1, height 24 px, border 1 px `#888888`, background `#FFFFFF`,
`#111111` text, placeholder `#999999`. Border turns `#C0392B` on invalid URL.  
Add button: 28×24 px, icon `ti-plus` 15 px, same border style as input.
Tooltip on add button: "Add to queue (Enter)".

Validation error: shown as a line of 11 px red text immediately below the
input row, left-aligned with the input (not the label). No dialog boxes.
Two error messages:
- "Not a recognised YouTube or YouTube Music link"
- "Update playlist mode requires a playlist link"

Enter key in the URL field triggers Add. Clears the field on successful add.

### 5.4 Save-to row (shown in Downloader tab as read-only reference)

Label: "Save to:"  
Read-only text input showing current download folder.  
Folder browse button: 28×24 px, icon `ti-folder`.  
Tooltip: "Change download folder".  
Clicking opens `QFileDialog.getExistingDirectory`.  
Change is applied immediately and saved to config.

### 5.5 Queue section

Label: "Queue — N:" (N = count, updates live).  
The queue list sits to the right of the label, full remaining width.

**Empty state:**
A rounded rectangle (border 1 px dashed `#CCCCCC`, background `#FAFAFA`),
containing centred text:
- Icon `ti-playlist`, 28 px, `#CCCCCC`
- "No items in queue", 12 px, `#AAAAAA`
- "Paste a link above and press + to add", 11 px, `#AAAAAA`

**Queue rows:**
Each row is a QFrame with background `#FFFFFF`, border 1 px `#D0D0D0`,
border-radius 2 px, padding 7 px. Gap between rows: 4 px.

Row layout (left to right):
- Status icon (15 px): see state table below
- Vertical stack:
  - Title (12 px, `#111111`, font-weight 500, elided at right)
  - Subtitle (11 px, `#666666`): type · track count · status detail
  - Progress bar (if downloading): 4 px tall, `#2980B9` fill on `#E0E0E0`
    track, shown only when status = DOWNLOADING
  - Retry button (if status = PAUSED_NETWORK): 11 px, inline below subtitle
- Mode tag (right side, small): "New" or "Update", 10 px, muted
- Remove / cancel button: `ti-x`, 13 px, `#BBBBBB`, hover `#C0392B`

Row border changes by state:
| Status             | Left border accent | Background         |
|--------------------|--------------------|--------------------|
| QUEUED             | none               | `#FFFFFF`          |
| DOWNLOADING        | 3 px `#4A90D9`     | `#F4F9FF`          |
| DONE               | none               | `#FFFFFF`, 65% opacity |
| SKIPPED_DUPLICATE  | none               | `#FFFFFF`, 65% opacity |
| PAUSED_NETWORK     | 3 px `#E67E22`     | `#FFFBF5`          |
| ERROR / SKIPPED    | 3 px `#C0392B`     | `#FFF8F8`          |
| CANCELLED          | none               | `#FFFFFF`, 65% opacity |

Status icons:
| Status             | Icon              | Colour        |
|--------------------|-------------------|---------------|
| QUEUED             | `ti-clock`        | `#999999`     |
| DOWNLOADING        | `ti-loader-2`     | `#2980B9`     |
| DONE               | `ti-circle-check` | `#27AE60`     |
| SKIPPED_DUPLICATE  | `ti-circle-check` | `#27AE60`     |
| PAUSED_NETWORK     | `ti-wifi-off`     | `#E67E22`     |
| ERROR / SKIPPED    | `ti-alert-circle` | `#C0392B`     |
| CANCELLED          | `ti-x`            | `#AAAAAA`     |

Maximum visible rows without scroll: 4. Beyond 4 rows: the list scrolls.
`QScrollArea` with no horizontal scroll bar, vertical scroll bar auto.

### 5.6 Error panel

Shown below the queue list when any item has status ERROR or SKIPPED (content
error, after all retries).

Header bar: background `#FDE8E8`, border 1 px `#C0392B`, text `#922B21`,
12 px. Left icon `ti-alert-triangle`. Right: `ti-chevron-down` / `ti-chevron-up`
(panel is collapsible).

Body (when expanded): background `#FFFFFF`, border same as header (no top
border, continues from header). Each error entry:
- Title (12 px, `#111111`, bold): track name
- Reason (11 px, `#C0392B`): error description
- Timestamp (11 px, `#999999`)
- Divider between entries: 1 px `#EEEEEE`

"Copy error log" button: bottom-right of panel body, 11 px, copies all
entries as plain text to clipboard.

### 5.7 Dependency status line

Shown at bottom of the form body, above the button bar.
Border-top: 1 px `#CCCCCC`. Padding-top: 6 px.
Icon: `ti-circle-check` green if all OK, `ti-alert-circle` amber if any issue.
Text: "yt-dlp v2026.06.10 · ffmpeg v7.1.1 — ready", 11 px, `#666666`.

### 5.8 Button bar

Two full-width buttons side by side. Height 30 px. Padding: 10 px horizontal,
10 px top, 12 px bottom.

Idle queue / done:
- Left: "Start queue" — primary style (background `#DAE8F8`, border `#4A90D9`,
  text `#1A5A9C`). Disabled (greyed, not clickable) when queue is empty.
- Right: "Clear all" — standard style.

Active download:
- Left: "Pause"
- Right: "Cancel all" — danger style (border `#C0392B`, text `#C0392B`,
  background `#FFF8F8`, hover `#FDE8E8`)

### 5.9 Progress bars

Two labelled Windows-style progress bars at the very bottom of the window.
Each has a label row above it (left: description, right: value) in 11 px
`#555555` text.

Progress bar styling: background `#FFFFFF`, border 1 px `#BBBBBB`,
border-radius 2 px, height 18 px. Fill: `#4A90D9` (item bar), `#27AE60`
(overall bar).

Row 1: "Item progress — {title}", right: "47% · 1.8 MB/s"  
Row 2: "Overall progress", right: "Item 2 of 3"

Both bars hidden (zero height, not just transparent) when no download is
active. They appear when a download starts.

---

## 6. Settings Tab

Same fixed-label form layout as Downloader tab (120 px labels, right-aligned).

### 6.1 Form rows

**Download folder:**  
Label: "Download folder:"  
Read-only input + folder browse button (`ti-folder`). Same as Downloader 5.4.

**Filename pattern:**  
Label: "Filename pattern:"  
`QComboBox`, full width. One option for v1: `%(title)s - %(artist)s`.
Do not change this default. Do not reorder it.

**Audio quality:**  
Label: "Audio quality:"  
`QComboBox`. One option: "Best available (--audio-quality 0)".

### 6.2 Post-processing groupbox

Groupbox title: "Post-processing".  
Two checkboxes:
- "Embed thumbnail (square-crop)" — checked by default
- "Embed metadata" — checked by default

Groupbox style: border 1 px `#AAAAAA`, border-radius 3 px, title inset at
top-left on the border, background `#FAFAFA`.

### 6.3 Dependencies groupbox

Groupbox title: "Dependencies".  
Two dependency cards side by side (equal width, gap 8 px).

Each card:
- Background `#FAFAFA`, border 1 px `#CCCCCC`, border-radius 3 px, padding
  10 px 12 px
- Header row: name (12 px, font-weight 500) + status pill (right-aligned)
- Version text: 11 px, `#666666`
  - Up to date: "v2026.06.10"
  - Update available: "v2026.05.18 → v2026.06.10" (arrow in amber `#E67E22`)
- Action button or progress bar (see states below)

Status pills:
| State              | Background    | Text colour   | Border        | Text              |
|--------------------|---------------|---------------|---------------|-------------------|
| Up to date         | `#D4EDDA`     | `#155724`     | `#C3E6CB`     | "up to date"      |
| Update available   | `#FFF3CD`     | `#856404`     | `#FFEAA7`     | "update available"|
| Checking           | `#E8E8E8`     | `#666666`     | `#CCCCCC`     | "checking..."     |
| Updating           | `#CCE5FF`     | `#004085`     | `#B8DAFF`     | "updating"        |

Pill style: font-size 10 px, font-weight 500, padding 2 px 8 px,
border-radius 99 px (fully rounded).

Action button states per card:
- Up to date: standard button "Check for update" + `ti-refresh` icon
- Update available: primary button "Update now" + `ti-download` icon
- Checking: button disabled, text "Checking..."
- Updating: no button; progress bar (3 px, `#2980B9` on `#E0E0E0`) +
  "Downloading — 71%" in 10 px `#2980B9` text below

### 6.4 Button bar

Two buttons. Height 30 px.
- Left: "Save settings" — primary style + `ti-device-floppy` icon
- Right: "Reset to defaults" — standard style + `ti-rotate-clockwise` icon

After clicking "Save settings": show a brief inline toast below the button
bar — "Settings saved", 11 px, `#27AE60`, auto-dismissed after 2 seconds.

---

## 7. About Tab

Centre-aligned vertically and horizontally within the tab body.

Top to bottom:
- App icon: 52×52 px, `#E8E8E8` background, 1 px `#CCCCCC` border,
  border-radius 6 px, `ti-music` icon 26 px `#555555` centred
- App name: "YT Music Downloader", 15 px, font-weight 500, `#111111`
- Version: "v1.0.0 · Windows x64", 11 px, `#888888`, margin-top 2 px,
  margin-bottom 12 px
- Author: "Built by Biraj Sarkar", 12 px, `#555555`. "Biraj Sarkar" in
  font-weight 500, `#222222`. Margin-bottom 14 px.
- Two buttons side by side (max-width 320 px combined), gap 8 px:
  - "GitHub — Biraj2004" + `ti-brand-github` icon 14 px
  - "Repository" + `ti-external-link` icon 14 px
  - Both standard button style. Clicking opens the URL in the default browser
    via `QDesktopServices.openUrl`.
  - URLs stored as `TODO_GITHUB_URL` and `TODO_REPO_URL` constants in
    `constants.py`. Clearly commented so they are trivial to find and update.
- Divider: 1 px `#DDDDDD`, full width, margin-top 14 px
- Note: "Built on yt-dlp (github.com/yt-dlp/yt-dlp) and ffmpeg (gyan.dev).
  For personal use only. Not affiliated with YouTube or Google."
  — 11 px, `#888888`, centred, line-height 1.7, margin-top 10 px

---

## 8. Setup Window (First Run)

A separate `QDialog` (modal, blocks main window from showing).  
Width: 480 px. Height: auto (fits content). Non-resizable.  
Title bar: same blue `#2D5FA8` as main window.

Body padding: 16 px.

**Intro text:** "YT Music Downloader needs two tools to work. Fetching them
from their official sources — this only happens once, or if a file goes
missing on launch." — 12 px, `#666666`, line-height 1.7, margin-bottom 12 px.

**Item list:** Two items separated by 1 px `#DDDDDD` dividers.

Each item (left to right):
- Status icon: 18 px
  - Pending: `ti-clock`, `#999999`
  - Downloading: `ti-loader-2`, `#2980B9`
  - Done: `ti-circle-check`, `#27AE60`
  - Error: `ti-alert-circle`, `#C0392B`
- Right block:
  - Name (12 px, font-weight 500, `#111111`) + source hint (10 px, `#888888`,
    e.g. "github.com/yt-dlp/yt-dlp")
  - Status text (11 px): green for done, blue for in-progress, red for error
  - Progress bar (3 px, visible only when status = downloading)

**Footer note:** "Files are saved to `bin/` next to the app. They are not
installed system-wide and do not touch the Windows registry."  
Background `#F5F5F5`, border 1 px `#DDDDDD`, border-radius 2 px, padding
7 px 10 px, 11 px `#666666`, `code` spans in background `#E0E0E0`.

**Bottom progress bar:** same Windows-style as main window. Label above:
"Download progress", right: percentage.

**Buttons (failure state only):**
- "Retry setup" — primary
- "Close app" — danger

On success: dialog closes automatically; main window appears.

---

## 9. Interactions and Keyboard

| Interaction                          | Action                                         |
|--------------------------------------|------------------------------------------------|
| Enter in URL field                   | Add to queue (same as clicking +)              |
| Escape                               | Clear URL field if not empty; else no action   |
| Click tab                            | Switch to that tab instantly                   |
| Click mode button                    | Activates that mode for next Add               |
| Click + / Enter with empty URL field | No action; no error                            |
| Click + with invalid URL             | Show validation error inline; do not add       |
| Click Start queue (queue empty)      | Button is disabled; no action                  |
| Click Start queue (queue has items)  | Start DownloadWorker for first QUEUED item     |
| Click Pause                          | Set pause flag; worker finishes current item   |
|                                      | then stops. Queue row stays QUEUED.            |
| Click Cancel all                     | Terminate active subprocess; mark all items    |
|                                      | CANCELLED                                      |
| Click × on queue row                 | If QUEUED: remove from queue                   |
|                                      | If DOWNLOADING: cancel that item               |
|                                      | If DONE/ERROR/CANCELLED: remove from list      |
| Click folder browse button           | Open system folder picker dialog               |
| Click Check for update (dep card)    | Run version check in background thread         |
| Click Update now (dep card)          | Run yt-dlp -U or ffmpeg re-download in thread  |
| Click Copy error log                 | Copy all error entries to clipboard as text    |
| Click GitHub / Repository (About)    | Open URL in system default browser             |
| Close window (✕)                     | Save window position/size to config; exit      |

---

## 10. Tooltips

All icon-only controls must have a tooltip. `setToolTip(text)` in Qt.

| Control                      | Tooltip text                    |
|------------------------------|---------------------------------|
| + (Add to queue button)      | "Add to queue (Enter)"          |
| Folder browse button         | "Change download folder"        |
| × (queue row remove/cancel)  | "Remove from queue" or "Cancel" |
| Settings tab icon (if used)  | "Settings"                      |
| About tab icon (if used)     | "About"                         |

---

## 11. Toast Notifications

Used for confirmations that do not require user action.

Implementation: a `QLabel` overlaid at the bottom of the window body,
shown with a fade-in, held for 2 seconds, then fade-out. Not a dialog.
Not a system notification. Purely in-window.

Style: background `#FFFFFF`, border 1 px `#CCCCCC`, border-radius 3 px,
padding 6 px 12 px, 12 px text, shadow none. Positioned at bottom-centre
of the window body.

Occasions:
- "Added to queue" — after successful add
- "Settings saved" — after save in Settings tab
- "Copied to clipboard" — after Copy error log

---

## 12. Icons

Use Tabler Icons (MIT licensed). Load as SVG or use the `qtawesome` package
which bundles Tabler Icons for Qt. Do not use emoji as icons.

Icon size: 13–16 px for inline controls, 18–22 px for status icons in
setup window, 26–28 px for the About logo.

Preferred icons (Tabler name → usage):
- `ti-download` — New download mode
- `ti-refresh` — Update playlist mode; Check for update
- `ti-plus` — Add to queue
- `ti-folder` — Browse folder
- `ti-x` — Remove / cancel / close
- `ti-player-play` — Start queue
- `ti-player-pause` — Pause
- `ti-clock` — Queued status
- `ti-loader-2` — Downloading / checking (animated spin if possible)
- `ti-circle-check` — Done / success
- `ti-alert-circle` — Error
- `ti-alert-triangle` — Error panel header
- `ti-wifi-off` — Network error / paused
- `ti-chevron-down` / `ti-chevron-up` — Collapse / expand error panel
- `ti-brand-github` — GitHub link
- `ti-external-link` — Repository link
- `ti-device-floppy` — Save settings
- `ti-rotate-clockwise` — Reset to defaults
- `ti-playlist` — Empty queue state
- `ti-music` — App logo (About tab, title bar)
- `ti-copy` — Copy error log

---

## 13. Disabled States

Disabled controls must look visually inactive, not just be non-clickable.
Use `setEnabled(False)` in Qt. Fusion style renders disabled controls with
greyed text and muted backgrounds automatically. Do not manually paint
disabled states — rely on Qt's built-in disabled palette.

Controls that must be disabled (not just hidden) when inactive:
- Start queue: disabled when queue is empty
- Pause: disabled when not downloading
- Cancel all: disabled when not downloading
- Clear all: disabled when queue is empty
- × on a DONE / CANCELLED row: enabled (to remove completed rows)
- Update now button: disabled while update is in progress

---

## 14. Window Behaviour

- Closing the window saves `window_x`, `window_y`, `window_w`, `window_h`
  to `config.json` before exit.
- On next launch, the window is restored to that position and size.
- If the restored position would place the window entirely off-screen
  (all four corners outside any monitor), reset to centred on the primary
  monitor at default size (700 × 540).
- The window is resizable. Minimum size: 600 × 460 px.
- The queue list and error panel grow to fill available vertical space
  when the window is resized.
- The progress bar section at the bottom is fixed height; it does not grow.
