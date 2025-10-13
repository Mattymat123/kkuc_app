# Chat Widget - Deployment Guide

Simple embeddable script that loads your existing Next.js chat app in an iframe.

## Local Testing

### 1. Start Your Servers

```bash
# Terminal 1 - Start backend
cd KKUCAssistant/backend
poetry run python -m app.server

# Terminal 2 - Start frontend
cd KKUCAssistant/frontend
yarn dev
```

### 2. Test the Widget

Open `test.html` in your browser, or inject the script into any website:

**Browser Console Method:**
```javascript
var script = document.createElement('script');
script.src = 'http://localhost:8080/widget.js';
document.body.appendChild(script);
```

**Or serve widget.js locally:**
```bash
# In the chat-widget folder
python3 -m http.server 8080
```

Then inject on any website via browser console:
```javascript
var script = document.createElement('script');
script.src = 'http://localhost:8080/widget.js';
document.body.appendChild(script);
```

## Production Deployment

### 1. Deploy Backend

Deploy your FastAPI backend to any cloud provider:
- Railway
- Render
- AWS/GCP
- Heroku

Example backend URL: `https://your-backend.railway.app`

### 2. Deploy Frontend to Vercel

```bash
cd KKUCAssistant/frontend

# Update the backend URL in app/api/chat/route.ts
# Change: http://0.0.0.0:8000
# To: https://your-backend.railway.app

# Deploy to Vercel
vercel deploy --prod
```

Your frontend will be at: `https://your-app.vercel.app`

### 3. Update Widget Script

Edit `widget.js` line 11:
```javascript
const WIDGET_URL = 'https://your-app.vercel.app';
```

### 4. Host Widget Script

Upload `widget.js` to:
- Your own domain/CDN
- GitHub Pages
- Vercel static hosting
- Any static file host

### 5. Customers Use Your Widget

Customers add one line to their website:
```html
<script src="https://your-domain.com/widget.js"></script>
```

## Files

- `widget.js` - The embeddable script (update WIDGET_URL for production)
- `test.html` - Local testing page
- `README.md` - This file

## Notes

- No changes needed to your existing Next.js app
- The widget loads your full app in an iframe
- Your app already has the modal/widget UI built-in
- Just update URLs when deploying to production
