/**
 * Chat Widget - Embeddable Script
 * Simply loads your existing Next.js chat app in an iframe
 * 
 * For local testing: WIDGET_URL = 'http://localhost:3000'
 * For production: WIDGET_URL = 'https://your-app.vercel.app'
 */

(function() {
  // Configuration - Update this for production
  const WIDGET_URL = 'http://localhost:3000';
  
  // Prevent multiple instances
  if (window.chatWidgetLoaded) return;
  window.chatWidgetLoaded = true;

  // Create iframe
  const iframe = document.createElement('iframe');
  iframe.src = WIDGET_URL;
  iframe.style.cssText = `
    position: fixed;
    bottom: 0;
    right: 0;
    width: 100%;
    height: 100%;
    border: none;
    z-index: 999999;
  `;
  iframe.allow = 'clipboard-read; clipboard-write';

  // Add to page
  if (document.body) {
    document.body.appendChild(iframe);
  } else {
    document.addEventListener('DOMContentLoaded', () => {
      document.body.appendChild(iframe);
    });
  }

  console.log('Chat widget loaded from:', WIDGET_URL);
})();
