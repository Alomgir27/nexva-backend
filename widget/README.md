# Nexva Chat Widget

Modern, clean chat widget with green theme and modular architecture.

## 🎨 Features

- ✅ **Green Theme**: Matches your app's color scheme (#32f08c)
- ✅ **Custom Logo**: Uses your logo from public/images
- ✅ **Fullscreen Mode**: Expand chat to fullscreen
- ✅ **Voice Chat**: Real-time transcription with proper message storage
- ✅ **WebSocket Streaming**: Live response streaming
- ✅ **Human Support**: Request human assistance
- ✅ **Modular Architecture**: Easy to maintain and extend

## 📁 Structure

```
widget/
├── widget.js              # Entry point
├── demo.html              # Demo page
└── src/
    ├── config.js          # Configuration management
    ├── styles.js          # Green theme styles
    ├── ui.js              # DOM creation & fullscreen
    ├── messaging.js       # Message display logic
    ├── websocket.js       # WebSocket connection
    ├── voice.js           # Voice chat with storage
    ├── utils.js           # Utility functions
    └── nexva-chat.js      # Main orchestrator
```

## 🚀 Usage

### Basic Setup

```html
<script type="module" src="widget/widget.js"></script>
<script type="module">
  NexvaChat.init('YOUR_API_KEY', {
    apiUrl: 'http://localhost:8000',
    logoUrl: '/images/img.png',
    primaryColor: '#32f08c'
  });
</script>
```

### Full Configuration

```javascript
NexvaChat.init('YOUR_API_KEY', {
  apiUrl: 'http://localhost:8000',
  position: 'bottom-right',           // bottom-right, bottom-left, top-right, top-left
  primaryColor: '#32f08c',            // Your brand color
  logoUrl: '/images/img.png',         // Your logo path
  welcomeMessage: 'Hi! How can I help you today?',
  placeholder: 'Type your message...',
  enableVoice: true,                  // Enable voice chat
  enableHumanSupport: true,           // Show "Talk to Human" button
  theme: 'dark',                      // dark or light
  autoOpen: false                     // Auto-open on page load
});
```

## 🎤 Voice Chat

Voice chat now works like the playground:
- Shows user message in real-time as you speak
- Updates message content while listening
- Sends message after 2 seconds of silence
- Removes message if nothing was said
- Properly stores both user prompts and assistant responses

## 🖥️ Fullscreen Mode

Click the fullscreen icon in the header to expand the chat to fullscreen.

## 🎨 Design

- **Colors**: Dark theme with green accents (#32f08c)
- **Background**: #0a0b0d (base), #121314 (secondary)
- **Text**: #f5f9fe (default), #a6aab5 (secondary)
- **Borders**: rgba(255, 255, 255, 0.06)
- **Rounded corners**: Modern 12-16px radius
- **Smooth animations**: 0.3s ease transitions

## 📦 Module Details

### `config.js`
- Default: Green theme, dark mode, logo support
- Manages all widget settings

### `styles.js`
- Green color scheme matching your app
- Dark theme with proper contrast
- Custom scrollbar styling
- Fullscreen support

### `ui.js`
- Logo in chat button and header
- Fullscreen icon next to close button
- Clean header with proper spacing

### `voice.js`
- Real-time message updates (like playground)
- Proper message storage
- Auto-send after silence
- Error handling

### `messaging.js`
- Green user bubbles
- Dark assistant bubbles
- Typing indicators
- Auto-scroll

## 🧪 Testing

**Important**: ES6 modules require a web server. You cannot open `demo.html` directly in the browser.

### Run Local Server

```bash
# Option 1: Use the provided script
cd widget
./serve.sh

# Option 2: Python 3
python3 -m http.server 8080

# Option 3: Node.js
npx http-server -p 8080

# Option 4: PHP
php -S localhost:8080
```

Then open: `http://localhost:8080/demo.html`

## 🔧 Customization

To change colors, edit `src/styles.js`:
```javascript
const primaryColor = config.primaryColor;  // #32f08c
const hoverColor = '#0fdc78';
```

To use a different logo, pass it in config:
```javascript
NexvaChat.init('API_KEY', {
  logoUrl: '/path/to/your/logo.png'
});
```


