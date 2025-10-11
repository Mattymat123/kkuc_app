# Testing the Widget on External Websites

## Common Issues & Solutions

### ERR_BLOCKED_BY_CLIENT Error

This error means your browser extension (ad blocker, privacy extension) is blocking the script.

**Solutions:**

1. **Disable ad blocker temporarily** for testing
   - Click your ad blocker icon
   - Disable it for the current site
   - Reload and try again

2. **Use the bookmarklet method instead:**
   - Create a new bookmark in your browser
   - Name it: "Load Chat Widget"
   - URL: `javascript:(function(){var s=document.createElement('script');s.src='http://localhost:8080/widget.js';document.body.appendChild(s);})();`
   - Click the bookmark on any website to inject the widget

3. **Paste code correctly in console:**
   Make sure to paste all 3 lines at once:
   ```javascript
   var script = document.createElement('script');
   script.src = 'http://localhost:8080/widget.js';
   document.body.appendChild(script);
   ```
   
   Or as a single line:
   ```javascript
   var script = document.createElement('script'); script.src = 'http://localhost:8080/widget.js'; document.body.appendChild(script);
   ```

## Step-by-Step Testing

1. **Start all servers:**
   ```bash
   # Terminal 1 - Backend
   cd langserve-assistant-ui/backend
   poetry run python -m app.server
   
   # Terminal 2 - Frontend
   cd langserve-assistant-ui/frontend
   yarn dev
   
   # Terminal 3 - Widget server
   cd chat-widget
   python3 -m http.server 8080
   ```

2. **Test on external website:**
   - Go to any website (e.g., example.com)
   - Open browser console (F12)
   - Disable ad blocker if needed
   - Paste the single-line code:
     ```javascript
     var script = document.createElement('script'); script.src = 'http://localhost:8080/widget.js'; document.body.appendChild(script);
     ```
   - Press Enter

3. **Verify it works:**
   - You should see: "Chat widget loaded from: http://localhost:3000" in console
   - The chat widget should appear as a full-screen overlay

## Alternative: Test on a Simple Local Page

If ad blockers keep blocking, test on a simple local HTML page first:

```bash
cd chat-widget
python3 -m http.server 8080
# Open http://localhost:8080/test.html
```

## Production Deployment

When deployed to production with HTTPS, these ad blocker issues will be resolved because:
- The script will be served from your domain (not localhost)
- HTTPS is more trusted by browsers
- Professional hosting is less likely to be blocked
