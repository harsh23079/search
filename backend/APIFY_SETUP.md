# Apify Token Setup

To use Instagram scraping, you need to set up an Apify token.

## Steps:

1. **Get your Apify token:**
   - Go to https://console.apify.com/
   - Sign up or log in
   - Navigate to Settings → Integrations
   - Copy your API token

2. **Set the environment variable:**

   **Option A: Create a `.env` file in the `backend` directory:**
   ```
   APIFY_TOKEN=your_token_here
   ```

   **Option B: Set it in PowerShell (Windows):**
   ```powershell
   $env:APIFY_TOKEN="your_token_here"
   ```

   **Option C: Set it when running the server:**
   ```powershell
   $env:APIFY_TOKEN="your_token_here"; python main.py
   ```

3. **Restart your backend server** after setting the token.

## Verify it's working:

Check the backend logs when starting - you should see:
- "Scrapers initialized successfully" (instead of a warning about APIFY_TOKEN)

If you see the warning, the token is not being loaded correctly.

