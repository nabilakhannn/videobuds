---
name: Blotato Posting Best Practices
description: Guidelines for generating contextual captions and uploading local media to Blotato
---

# Blotato Best Practices

When tasked with posting via Blotato, the Agent must adhere to these best practices to ensure high-quality and directly hosted content.

---

## 1. Contextual Caption Generation

You must **never** post a generic, default caption. How you generate the caption depends on the **media type** (image vs. video).

### For Images
1. Call `view_file` on the image path.
2. The system will provide an inline display of the visual elements.
3. Analyze the aesthetics, tone, setting, and subjects of the image.
4. Write a high-quality, engaging caption tailored to the specific content, including relevant emojis, hashtags, and a clear call-to-action (e.g., "Tag your travel buddy!").

### For Videos
**You CANNOT visually analyze video files.** The `view_file` tool does not support `.mp4` and similar video formats — it will throw an "unsupported mime type" error. Do NOT attempt it.

Instead, follow this fallback flow to gather enough context for a great caption:

1. **Check for a brand file first.** Look for any `*_BRAND.md` file in the `references/` folder. If one exists, read it and use the brand voice, tone, and audience to craft the caption.
2. **If no brand file exists, ask the user.** Prompt them with something like:
   > "I can't peek inside videos directly — could you give me a quick description of what's in this video? Or point me to a brand guidelines file? That way I can write a caption that really nails the vibe."
3. **Use whatever context is available.** The filename, the user's request, any accompanying notes, and the target platforms all provide clues. For example, a file called `gym_motivation_clip.mp4` tells you the general theme even without watching it.
4. **Tailor to each platform.** Even with the same video, the caption style should differ:
   - **Instagram Reels**: Emoji-rich, hook-first, 3-5 hashtags, call-to-action
   - **TikTok**: Casual, trend-aware, shorter, 2-3 hashtags max
   - **YouTube Shorts**: Descriptive title (provided via `title` field), minimal caption, keyword-focused

---

## 2. Getting Media Into Blotato

Blotato needs a **URL** for any media you want to post. How you get that URL depends on where the media currently lives.

### Decision Logic (FOLLOW THIS ORDER)

```
Does the media already have a public URL?
  (e.g., Airtable attachment, Kie.ai hosted, any web URL)
  → YES: Pass the URL directly to mediaUrls ← PREFERRED (Method 0)
  → NO (it's a local file only):
      Is the file a VIDEO (.mp4, .mov, .webm)?
        → YES: Is KIE_API_KEY set in .env?
            → YES: Use Kie.ai upload (Method A)
            → NO:  Use Blotato base64 upload (Method B)
        → NO (it's an image): Use Blotato base64 upload (Method B)
```

---

### Method 0: Direct URL Passthrough ← PREFERRED

**This is the fastest, simplest method — always try this first.**

Blotato's `mediaUrls` parameter accepts **any publicly accessible URL**. Blotato fetches the image/video **immediately when the post is submitted** (not when it's eventually published), then stores it on their own servers. This means even **temporary URLs work** — including Airtable CDN links that expire after a few hours.

**When to use:**
- Images from Airtable's `Generated Image 1` attachment field (the `v5.airtableusercontent.com` URLs)
- Kie.ai hosted URLs (`tempfile.redpandaai.co`)
- Any other public image/video URL from the web

**How it works:**
1. Get the public URL from wherever the media is hosted (Airtable, Kie.ai, etc.)
2. Pass it directly to `mediaUrls` in `mcp_blotato_blotato_create_post`
3. That's it — no upload step needed

**Example (Airtable → Blotato, no upload):**
```python
# Fetch record from Airtable
record = get_records("AND({Index}=59)")[0]
img_url = record['fields']['Generated Image 1'][0]['url']
caption = record['fields']['Caption']

# Schedule directly — Blotato fetches the image immediately
mcp_blotato_blotato_create_post(
    accountId="...",
    platform="instagram",
    text=caption,
    mediaUrls=[img_url],
    scheduledTime="2026-03-01T23:00:00Z"
)
```

**Why temporary URLs are fine:** Blotato grabs the image the moment you submit the post. Even if the Airtable URL expires 2 hours later, Blotato already has the image stored on their servers. So scheduling a post for next week with a temporary URL works perfectly.

**⚠️ The only risk:** If the URL is already expired or invalid *at the time of submission*, the post will fail. Always use fresh URLs — don't cache Airtable URLs across sessions.

---

### Method A: Kie.ai Upload (for Local Videos)

Only use this when you have a **local video file** with no existing public URL. Kie.ai uses multipart file upload — it streams the raw binary directly, no base64 bloat. Handles large video files better than base64.

**How it works:**
1. Upload the video file via `tools/kie_upload.py` (uses `KIE_API_KEY` from `.env`)
2. Get back a public URL (hosted at `tempfile.redpandaai.co`)
3. Pass that URL to `mediaUrls` in `mcp_blotato_blotato_create_post`

**Code (inline Python — always save URL to a file):**
```python
python -c "
import sys; sys.path.insert(0, '.')
from dotenv import load_dotenv; load_dotenv('references/.env')
from tools.kie_upload import upload_reference
url = upload_reference('references/inputs/video.mp4')
f = open('references/outputs/uploaded_url.txt', 'w'); f.write(url); f.close()
print('Saved.')
"
```
Then read the URL from the output file with `view_file`.

**For multiple videos:**
```python
python -c "
import sys; sys.path.insert(0, '.')
from dotenv import load_dotenv; load_dotenv('references/.env')
from tools.kie_upload import upload_references
urls = upload_references(['references/inputs/v1.mp4', 'references/inputs/v2.mp4', 'references/inputs/v3.mp4'])
f = open('references/outputs/uploaded_urls.txt', 'w'); f.write('\n'.join(urls)); f.close()
print('Saved.')
"
```

**⚠️ Kie.ai URLs expire after 3 days**, but this doesn't matter — Blotato fetches immediately on submission (see Method 0).

---

### Method B: Blotato Base64 Upload (Fallback for Local Files)

Only use this when you have a **local file** and either (a) it's an image, or (b) Kie.ai is unavailable. Uploads the file to Blotato's `https://backend.blotato.com/v2/media` endpoint using base64 encoding.

**Downsides:** Base64 increases file size by ~33% and can struggle with large files (50MB+).

**Steps:**
1. Read the local file and encode it in `base64`.
2. Format the `url` body field with the correct **data URI scheme** (see MIME types below).
3. `POST` to `https://backend.blotato.com/v2/media` with the API key in the `blotato-api-key` header.
4. Extract the public URL from the JSON response.
5. Pass that URL to the `mediaUrls` field in `mcp_blotato_blotato_create_post`.

### MIME Types — Pick the Right One
| File Extension | Data URI Prefix |
|---------------|----------------|
| `.jpg` / `.jpeg` | `data:image/jpeg;base64,` |
| `.png` | `data:image/png;base64,` |
| `.gif` | `data:image/gif;base64,` |
| `.webp` | `data:image/webp;base64,` |
| `.mp4` | `data:video/mp4;base64,` |
| `.mov` | `data:video/quicktime;base64,` |
| `.webm` | `data:video/webm;base64,` |

**CRITICAL:** Using the wrong MIME type (e.g., `image/jpeg` for an `.mp4`) will cause silent failures or corrupt uploads. Always match the extension.

### Upload Script Template (PowerShell) — Single File

**IMPORTANT:** Always write this as a `.ps1` script file, then run it with `powershell -ExecutionPolicy Bypass -File <path>`. Do NOT try to inline this as a one-liner with `powershell -Command "..."` — the nested quotes and variable interpolation will break.

**CRITICAL:** Always save the resulting URL to a **text file** — never rely on terminal output (`Write-Output` / `Write-Host`). Long URLs get truncated and line-wrapped in the terminal, making them impossible to extract reliably.

```powershell
# === Blotato Media Upload Script (Single File) ===
# Save this as a .ps1 file and run with:
#   powershell -ExecutionPolicy Bypass -File "path\to\script.ps1"

$path = "C:\path\to\file.mp4"
$mimeType = "video/mp4"  # Change to match the file type (see MIME table above)
$outFile = "C:\path\to\outputs\uploaded_url.txt"  # Where to save the resulting URL

$base64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($path))
$dataUri = "data:${mimeType};base64,$base64"
$body = @{ url = $dataUri } | ConvertTo-Json
$headers = @{ "blotato-api-key" = $env:BLOTATO_API_KEY }

$res = Invoke-RestMethod -Uri "https://backend.blotato.com/v2/media" -Method Post -Headers $headers -Body $body -ContentType "application/json"
$res.url | Set-Content $outFile -Encoding UTF8
Write-Host "URL saved to $outFile"
```

After reading the URL from the output file, **delete the temp script** to keep the project clean:
```powershell
Remove-Item "path\to\script.ps1" -Force
```

### Upload Script Template (PowerShell) — Multiple Files (Batch)

When uploading multiple files (e.g., scheduling a series of videos), use this batch template. It loops through all files and saves every URL to a single text file, one URL per line, in order.

```powershell
# === Blotato Batch Media Upload Script ===
# Save this as a .ps1 file and run with:
#   powershell -ExecutionPolicy Bypass -File "path\to\script.ps1"

$apiKey = $env:BLOTATO_API_KEY  # Or hardcode from .env if $env isn't loaded
$mimeType = "video/mp4"  # Change to match file type
$outFile = "C:\path\to\outputs\uploaded_urls.txt"

$files = @(
    "C:\path\to\video1.mp4",
    "C:\path\to\video2.mp4",
    "C:\path\to\video3.mp4"
)

$urls = @()
foreach ($file in $files) {
    Write-Host "Uploading: $(Split-Path $file -Leaf) ..."
    $base64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($file))
    $dataUri = "data:${mimeType};base64,$base64"
    $body = @{ url = $dataUri } | ConvertTo-Json
    $headers = @{ "blotato-api-key" = $apiKey }

    try {
        $res = Invoke-RestMethod -Uri "https://backend.blotato.com/v2/media" -Method Post -Headers $headers -Body $body -ContentType "application/json"
        $urls += $res.url
        Write-Host "Done."
    } catch {
        $urls += "FAILED"
        Write-Host "FAILED: $_"
    }
}

$urls | Set-Content $outFile -Encoding UTF8
Write-Host "`nAll $($urls.Count) URLs saved to $outFile"
```

After reading the URLs, **delete the temp script and optionally the URL file**:
```powershell
Remove-Item "path\to\script.ps1" -Force
```

---

### Known Gotchas (Lessons Learned)

1. **Always try URL passthrough first (Method 0).** Don't download-and-reupload media that already has a public URL. Blotato fetches immediately on submission, so even temporary Airtable CDN URLs work.
2. **Airtable URLs are temporary but that's OK.** They expire after a few hours, but Blotato grabs them instantly. Just don't cache Airtable URLs across sessions — always fetch fresh ones.
3. **Never inline complex PowerShell as `-Command` strings.** The double-quote escaping around `data:video/mp4;base64,$base64` will fail with "Missing argument in parameter list". Always use a `.ps1` script file instead.
4. **`-MaximumRetryCount` doesn't exist in older PowerShell.** Don't use it with `Invoke-RestMethod`. If you need retries, wrap the call in a manual loop.
5. **NEVER rely on terminal output for URLs.** Long Blotato URLs (~140+ chars) get truncated, wrapped, and mangled in terminal output. This causes silent failures when you try to use the URL. Always save URLs to a **text file** using `Set-Content`, then read the file with `view_file`. This is the #1 cause of wasted re-uploads.
6. **File size limit.** Base64 encoding increases file size by ~33%. Files under ~10 MB should work fine. For very large videos (50MB+), consider an alternative upload method.
7. **Always clean up.** Delete any temporary `.ps1` upload scripts after use — never leave throwaway scripts in the project.
8. **Batch uploads can be slow.** Each video upload takes 30-90 seconds depending on file size. For 3+ videos, expect the script to run for several minutes. Be patient and don't kill the process early.

---

## 3. Platform-Specific Posting Requirements

When posting the same media to multiple platforms, remember each platform has different required fields. Always call `mcp_blotato_blotato_list_accounts` first. Here's a quick reference:

| Platform | Key Required Fields |
|----------|-------------------|
| **Instagram** | `mediaType` must be `"reel"` for videos |
| **TikTok** | `privacyLevel`, `disabledComments`, `disabledDuet`, `disabledStitch`, `isBrandedContent`, `isYourBrand`, `isAiGenerated` — all required |
| **YouTube** | `title` (required), `privacyStatus`, `shouldNotifySubscribers` |
| **Twitter** | No extra fields needed |
| **LinkedIn** | Optional `pageId` for company pages |

### TikTok Defaults (for non-branded, human-created content)
```
privacyLevel: "PUBLIC_TO_EVERYONE"
disabledComments: false
disabledDuet: false
disabledStitch: false
isBrandedContent: false
isYourBrand: false
isAiGenerated: false
```

---

## 4. Scheduling Timezone Quick Reference

Blotato's `scheduledTime` field requires **ISO 8601 UTC** format (e.g., `2026-02-24T01:00:00Z`). When a user asks to schedule at a local time, convert to UTC using these offsets:

| City / Zone | UTC Offset | 12:00 PM local → UTC |
|-------------|-----------|---------------------|
| **Sydney (AEDT)** | UTC+11 | `01:00:00Z` |
| **Sydney (AEST)** | UTC+10 | `02:00:00Z` |
| **Tokyo (JST)** | UTC+9 | `03:00:00Z` |
| **London (GMT)** | UTC+0 | `12:00:00Z` |
| **London (BST)** | UTC+1 | `11:00:00Z` |
| **New York (EST)** | UTC-5 | `17:00:00Z` |
| **New York (EDT)** | UTC-4 | `16:00:00Z` |
| **Los Angeles (PST)** | UTC-8 | `20:00:00Z` |
| **Los Angeles (PDT)** | UTC-7 | `19:00:00Z` |

**Tip:** The user's current local time is always provided in the metadata (e.g., `2026-02-23T15:36:43+11:00`). The `+11:00` suffix tells you the offset directly — just subtract that from the target time to get UTC.

**Daylight Saving Gotcha:** Sydney switches between AEDT (+11) and AEST (+10). Always check the offset from the metadata timestamp rather than assuming.

---

## 5. Post Status Polling (MANDATORY)

**HARD RULE: After submitting a post via `mcp_blotato_blotato_create_post`, you MUST poll until every post reaches a terminal state (`published`, `scheduled`, or `failed`). NEVER stop while a post is still `in-progress`.**

### Polling Procedure

1. After submitting posts, immediately call `mcp_blotato_blotato_get_post_status` for each post.
2. If any post is still `in-progress`, **wait ~30 seconds** (use `Start-Sleep -Seconds 30` or equivalent), then poll again.
3. **Repeat** until every post has reached a terminal state.
4. Once all posts are resolved, report the final results to the user in a clear summary table:

#### On Success (`published`)
```
✅ Instagram — Published! → [publicUrl]
✅ TikTok — Published! → [publicUrl]
✅ YouTube — Published! → [publicUrl]
```

#### On Failure (`failed`)
```
❌ Instagram — Failed: [errorMessage]
```
Inform the user of the specific error so they can take action (e.g., re-authenticate, fix content, etc.).

#### On Scheduled (`scheduled`)
```
📅 Instagram — Scheduled for [scheduledTime]
```

### Timing Guide
- **Images** typically resolve in 10–20 seconds.
- **Videos** can take 1–5 minutes due to platform transcoding.
- Be patient — video posts especially on YouTube and TikTok take longer.
- Maximum polling duration: **10 minutes**. If still `in-progress` after 10 minutes, inform the user and provide the submission IDs so they can check manually.

### Example Flow
```
Post submitted → poll at 0s → in-progress
                → wait 30s → poll → in-progress
                → wait 30s → poll → published ✅ → report to user
```

**The user should NEVER have to ask "is it done yet?" — you proactively track it and tell them.**
