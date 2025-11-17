export const Config = {
  defaults: {
    apiUrl: 'http://localhost:8000',
    position: 'bottom-right',
    primaryColor: '#32f08c',
    headerText: 'Nexva',
    welcomeMessage: 'Hi! How can I help you today?',
    placeholder: 'Type your message...',
    enableVoice: true,
    enableHumanSupport: true,
    autoOpen: false,
    theme: 'light',
    borderRadius: '12px',
    buttonIcon: 'chat',
    buttonSize: '60px',
    buttonColor: null
  },
  
  init: function(apiKey, options) {
    options = options || {};
    const primaryColor = options.primaryColor || this.defaults.primaryColor;
    return {
      apiKey: apiKey,
      apiUrl: options.apiUrl || this.defaults.apiUrl,
      position: options.position || this.defaults.position,
      primaryColor: primaryColor,
      headerText: options.headerText || this.defaults.headerText,
      welcomeMessage: options.welcomeMessage || this.defaults.welcomeMessage,
      placeholder: options.placeholder || this.defaults.placeholder,
      enableVoice: options.enableVoice !== false,
      enableHumanSupport: options.enableHumanSupport !== false,
      autoOpen: options.autoOpen || false,
      theme: options.theme || this.defaults.theme,
      borderRadius: options.borderRadius || this.defaults.borderRadius,
      buttonIcon: options.buttonIcon || this.defaults.buttonIcon,
      buttonSize: options.buttonSize || this.defaults.buttonSize,
      buttonColor: options.buttonColor || primaryColor
    };
  }
};

export const Utils = {
  escapeHtml: function(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  },
  
  generateSessionId: function() {
    return 'widget-' + Date.now();
  },
  
  saveConversationId: function(apiKey, conversationId) {
    try {
      if (!conversationId) {
        console.warn('Cannot save null conversation ID');
        return;
      }
      const key = `nexva_conv_${apiKey}`;
      sessionStorage.setItem(key, conversationId.toString());
    } catch (e) {
      console.error('Failed to save conversation ID:', e);
    }
  },
  
  getConversationId: function(apiKey) {
    try {
      const key = `nexva_conv_${apiKey}`;
      const value = sessionStorage.getItem(key);
      return value ? parseInt(value, 10) : null;
    } catch (e) {
      console.error('Failed to get conversation ID:', e);
      return null;
    }
  },
  
  clearConversation: function(apiKey) {
    try {
      const key = `nexva_conv_${apiKey}`;
      sessionStorage.removeItem(key);
    } catch (e) {
      console.error('Failed to clear conversation:', e);
    }
  }
};

export const UI = {
  isFullscreen: false,
  isDocked: false,
  fullscreenIcon: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/></svg>',
  fullscreenExitIcon: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/></svg>',
  dockIcon: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M21 3H3c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h18c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM3 19V5h11v14H3zm18 0h-5V5h5v14z"/></svg>',
  dockExitIcon: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 3h11v11H3zm7 2H5v7h5V5zm4 0v7h5V5h-5zM3 15h11v6H3zm7 2H5v2h5v-2zm4 0v2h5v-2h-5z"/></svg>',
  
  createWidget: function(config) {
    const container = document.createElement('div');
    container.className = 'nexva-chat-container';
    container.innerHTML = `
      <button class="nexva-chat-button" id="nexvaChatButton" aria-label="Open chat">
        <svg viewBox="0 0 24 24" fill="white" width="28" height="28">
          <path d="M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM6 9h12v2H6V9zm8 5H6v-2h8v2zm4-6H6V6h12v2z"/>
        </svg>
      </button>
      <div class="nexva-chat-window" id="nexvaChatWindow">
        <div class="nexva-chat-header">
          <div class="nexva-chat-header-top">
            <div class="nexva-chat-header-title">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/>
              </svg>
              <h3>${config.headerText}</h3>
            </div>
            <div class="nexva-chat-header-actions">
            <button class="nexva-chat-icon-btn" id="nexvaDock" aria-label="Dock" title="Dock">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M21 3H3c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h18c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM3 19V5h11v14H3zm18 0h-5V5h5v14z"/></svg>
            </button>
            <button class="nexva-chat-icon-btn" id="nexvaFullscreen" aria-label="Maximize" title="Maximize">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/></svg>
            </button>
            <button class="nexva-chat-icon-btn nexva-chat-close" id="nexvaChatClose" aria-label="Close" title="Close">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
            </button>
            </div>
          </div>
          <div class="nexva-mode-switcher" id="nexvaModeSwitcher">
            <button class="nexva-mode-btn active" data-mode="ai" title="AI Assistant">
              <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
                <path d="M20.5 11H19V7c0-1.1-.9-2-2-2h-4V3.5C13 2.12 11.88 1 10.5 1S8 2.12 8 3.5V5H4c-1.1 0-1.99.9-1.99 2v3.8H3.5c1.49 0 2.7 1.21 2.7 2.7s-1.21 2.7-2.7 2.7H2V20c0 1.1.9 2 2 2h3.8v-1.5c0-1.49 1.21-2.7 2.7-2.7 1.49 0 2.7 1.21 2.7 2.7V22H17c1.1 0 2-.9 2-2v-4h1.5c1.38 0 2.5-1.12 2.5-2.5S21.88 11 20.5 11z"/>
              </svg>
            </button>
            <button class="nexva-mode-btn" data-mode="human" title="Human Support">
              <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
              </svg>
            </button>
          </div>
        </div>
        <div class="nexva-chat-messages" id="nexvaChatMessages">
          <div class="nexva-chat-message assistant">
            <div class="nexva-chat-message-content">${config.welcomeMessage}</div>
          </div>
        </div>
        <div class="nexva-chat-input-area">
          <div class="nexva-chat-actions" id="nexvaChatActions" style="display:none;"></div>
          <div class="nexva-chat-input-row" id="nexvaChatInputRow">
            ${config.enableVoice ? '<button class="nexva-chat-voice-btn" id="nexvaVoiceBtn" aria-label="Voice input" title="Click to start voice input" data-voice-active="false"><svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20"><path d="M12 15c1.66 0 2.99-1.34 2.99-3L15 6c0-1.66-1.34-3-3-3S9 4.34 9 6v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 15 6.7 12H5c0 3.42 2.72 6.23 6 6.72V22h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z"/></svg></button>' : ''}
            <input type="text" class="nexva-chat-input" id="nexvaChatInput" placeholder="${config.placeholder}" autocomplete="off">
            <button class="nexva-chat-btn" id="nexvaChatSend" aria-label="Send message" title="Send message">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
            </button>
          </div>
        </div>
      </div>
      <div class="nexva-chat-voice-indicator" id="nexvaVoiceIndicator">
        <div class="nexva-chat-voice-wave"><span></span><span></span><span></span><span></span></div>
        <span>Listening...</span>
      </div>
    `;
    document.body.appendChild(container);
  },
  
  toggleChat: function(isOpen) {
    const window = document.getElementById('nexvaChatWindow');
    console.log('[Nexva UI] toggleChat called, isOpen:', isOpen);
    console.log('[Nexva UI] Window element:', window);
    
    if (window) {
      if (isOpen) {
        window.classList.add('open');
        const input = document.getElementById('nexvaChatInput');
        if (input) input.focus();
        console.log('[Nexva UI] Window opened, classes:', window.className);
      } else {
        window.classList.remove('open');
        this.resetLayoutState();
        console.log('[Nexva UI] Window closed');
      }
    } else {
      console.error('[Nexva UI] Chat window element not found!');
    }
  },

  resetLayoutState: function() {
    const window = document.getElementById('nexvaChatWindow');
    const fullscreenBtn = document.getElementById('nexvaFullscreen');
    const dockBtn = document.getElementById('nexvaDock');
    const chatButton = document.getElementById('nexvaChatButton');
    
    this.isFullscreen = false;
    this.isDocked = false;
    
    if (window) {
      window.classList.remove('fullscreen', 'docked');
    }
    if (fullscreenBtn) {
      fullscreenBtn.innerHTML = this.fullscreenIcon;
      fullscreenBtn.setAttribute('title', 'Fullscreen');
    }
    if (dockBtn) {
      dockBtn.innerHTML = this.dockIcon;
      dockBtn.setAttribute('title', 'Dock');
    }
    if (chatButton) {
      chatButton.style.display = 'flex';
    }
  },
  
  toggleFullscreen: function() {
    const window = document.getElementById('nexvaChatWindow');
    const btn = document.getElementById('nexvaFullscreen');
    
    if (!window || !btn) {
      return;
    }
    
    if (this.isDocked) {
      this.toggleDock();
    }
    
    this.isFullscreen = !this.isFullscreen;
    
    if (this.isFullscreen) {
      window.classList.add('fullscreen');
      btn.innerHTML = this.fullscreenExitIcon;
      btn.setAttribute('title', 'Exit Fullscreen');
    } else {
      window.classList.remove('fullscreen');
      btn.innerHTML = this.fullscreenIcon;
      btn.setAttribute('title', 'Fullscreen');
    }
  },
  
  toggleDock: function() {
    const window = document.getElementById('nexvaChatWindow');
    const btn = document.getElementById('nexvaDock');
    const chatButton = document.getElementById('nexvaChatButton');
    
    if (!window || !btn || !chatButton) {
      return;
    }
    
    if (this.isFullscreen) {
      this.toggleFullscreen();
    }
    
    this.isDocked = !this.isDocked;
    
    if (this.isDocked) {
      window.classList.add('docked');
      chatButton.style.display = 'none';
      btn.innerHTML = this.dockExitIcon;
      btn.setAttribute('title', 'Undock');
    } else {
      window.classList.remove('docked');
      chatButton.style.display = 'flex';
      btn.innerHTML = this.dockIcon;
      btn.setAttribute('title', 'Dock');
    }
  },
  
  updateActions: function(config, conversationId, supportRequested, onRequestSupport) {
    if (!config.enableHumanSupport || !conversationId) {
      document.getElementById('nexvaChatActions').style.display = 'none';
      return;
    }
    
    const actionsDiv = document.getElementById('nexvaChatActions');
    actionsDiv.style.display = 'none';
  },
  
  updateMode: function(mode) {
    const buttons = document.querySelectorAll('.nexva-mode-btn');
    buttons.forEach(btn => {
      if (btn.dataset.mode === mode) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });
  },
  
  animateHeaderTitle: function(isListening, originalTitle) {
    const titleElement = document.querySelector('.nexva-chat-header-title h3');
    if (!titleElement) return;
    
    titleElement.style.transition = 'transform 0.3s ease, opacity 0.3s ease';
    
    if (isListening) {
      titleElement.style.transform = 'translateY(-20px)';
      titleElement.style.opacity = '0';
      
      setTimeout(() => {
        titleElement.innerHTML = `
          <div style="display: flex; align-items: center; gap: 12px;">
            <div class="nexva-chat-voice-wave"><span></span><span></span><span></span><span></span></div>
            <span>Listening...</span>
          </div>
        `;
        titleElement.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
          titleElement.style.transform = 'translateY(0)';
          titleElement.style.opacity = '1';
        }, 50);
      }, 300);
    } else {
      titleElement.style.transform = 'translateY(-20px)';
      titleElement.style.opacity = '0';
      
      setTimeout(() => {
        titleElement.textContent = originalTitle;
        titleElement.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
          titleElement.style.transform = 'translateY(0)';
          titleElement.style.opacity = '1';
        }, 50);
      }, 300);
    }
  }
};

export const Styles = {
  inject: function(config) {
    const style = document.createElement('style');
    const primaryColor = config.primaryColor;
    const hoverColor = '#0fdc78';
    const bgBase = '#0a0b0d';
    const bgSecondary = '#141517';
    const bgTertiary = '#1a1b1e';
    const bgOverlay = 'rgba(255, 255, 255, 0.03)';
    const textDefault = '#f5f9fe';
    const textSecondary = '#9ca3af';
    const borderColor = 'rgba(255, 255, 255, 0.08)';
    const position = config.position;
    const borderRadius = config.borderRadius;
    const buttonSize = config.buttonSize;
    const buttonColor = config.buttonColor;
    const buttonBorderRadius = config.borderRadius === '0px' ? '0px' : '50%';
    
    style.textContent = `
      * { box-sizing: border-box; }
      
      .nexva-chat-container { 
        position: fixed; 
        ${position.includes('bottom') ? 'bottom: 20px;' : 'top: 20px;'} 
        ${position.includes('right') ? 'right: 20px;' : 'left: 20px;'} 
        z-index: 999999; 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", sans-serif;
      }
      
      .nexva-chat-button { 
        width: ${buttonSize}; 
        height: ${buttonSize}; 
        background: linear-gradient(135deg, ${buttonColor} 0%, ${hoverColor} 100%); 
        border: none; 
        border-radius: ${buttonBorderRadius}; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        cursor: pointer; 
        box-shadow: 0 8px 24px rgba(15, 220, 120, 0.3); 
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
      }
      .nexva-chat-button:hover { 
        transform: translateY(-3px) scale(1.05); 
        box-shadow: 0 12px 32px rgba(15, 220, 120, 0.5); 
      }
      .nexva-chat-button:active {
        transform: translateY(-1px) scale(1.02);
      }
      .nexva-chat-button svg { 
        transition: transform 0.3s ease; 
      }
      .nexva-chat-button:hover svg { 
        transform: scale(1.1); 
      }
      
      .nexva-chat-window { 
        display: none; 
        position: fixed; 
        ${position.includes('bottom') ? 'bottom: 90px;' : 'top: 90px;'} 
        ${position.includes('right') ? 'right: 20px;' : 'left: 20px;'} 
        width: 400px; 
        height: 600px; 
        max-height: calc(100vh - 120px); 
        background: ${bgBase}; 
        border-radius: 16px; 
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6), 0 0 1px ${borderColor}; 
        flex-direction: column; 
        overflow: hidden; 
        backdrop-filter: blur(10px);
      }
      .nexva-chat-window.open { 
        display: flex; 
        animation: slideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1); 
      }
      .nexva-chat-window.fullscreen { 
        width: 100vw; 
        height: 100vh; 
        max-height: 100vh; 
        border-radius: 0; 
        top: 0; 
        bottom: 0; 
        left: 0; 
        right: 0; 
        box-shadow: none;
      }
      .nexva-chat-window.docked { 
        width: 400px; 
        height: 100vh; 
        max-height: 100vh; 
        border-radius: 0; 
        top: 0; 
        bottom: 0; 
        right: 0; 
        left: auto; 
        box-shadow: -4px 0 20px rgba(0, 0, 0, 0.3); 
        animation: slideInRight 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
      }
      
      @keyframes slideUp { 
        from { opacity: 0; transform: translateY(30px) scale(0.95); } 
        to { opacity: 1; transform: translateY(0) scale(1); } 
      }
      @keyframes slideInRight { 
        from { transform: translateX(100%); } 
        to { transform: translateX(0); } 
      }
      
      .nexva-chat-header { 
        background: ${bgSecondary}; 
        color: ${textDefault}; 
        padding: 16px; 
        display: flex; 
        flex-direction: column; 
        gap: 12px; 
        border-bottom: 1px solid ${borderColor}; 
      }
      
      .nexva-chat-header-top { 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        gap: 12px; 
      }
      
      .nexva-chat-header-title { 
        display: flex; 
        align-items: center; 
        gap: 10px; 
        overflow: hidden; 
        flex: 1; 
      }
      .nexva-chat-header-title svg { 
        flex-shrink: 0; 
        width: 20px; 
        height: 20px; 
        color: ${primaryColor}; 
      }
      .nexva-chat-header h3 { 
        margin: 0; 
        font-size: 15px; 
        font-weight: 600; 
        letter-spacing: -0.01em; 
        white-space: nowrap; 
        color: ${textDefault};
      }
      
      .nexva-chat-header-actions { 
        display: flex; 
        gap: 4px; 
        align-items: center; 
        flex-shrink: 0; 
      }
      
      .nexva-chat-icon-btn { 
        background: ${bgOverlay}; 
        border: none; 
        color: ${textSecondary}; 
        cursor: pointer; 
        padding: 0; 
        width: 36px; 
        height: 36px; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        transition: all 0.2s ease; 
        border-radius: 8px;
      }
      .nexva-chat-icon-btn:hover { 
        color: ${textDefault}; 
        background: rgba(255, 255, 255, 0.08); 
        transform: scale(1.05);
      }
      .nexva-chat-icon-btn:active {
        transform: scale(0.95);
      }
      .nexva-chat-icon-btn svg { 
        width: 18px; 
        height: 18px; 
      }
      .nexva-chat-close:hover { 
        color: #ef4444; 
        background: rgba(239, 68, 68, 0.1); 
      }
      
      .nexva-mode-switcher { 
        display: flex; 
        gap: 8px; 
        padding: 4px; 
        background: ${bgBase}; 
        border-radius: 10px; 
        width: 100%;
        border: 1px solid ${borderColor};
      }
      
      .nexva-mode-btn { 
        flex: 1; 
        background: transparent; 
        border: none; 
        padding: 10px 16px; 
        cursor: pointer; 
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        gap: 8px; 
        color: ${textSecondary}; 
        border-radius: 8px; 
        font-size: 14px;
        font-weight: 500;
        position: relative;
      }
      .nexva-mode-btn svg { 
        width: 18px; 
        height: 18px; 
      }
      .nexva-mode-btn:hover { 
        background: ${bgOverlay}; 
        color: ${textDefault}; 
      }
      .nexva-mode-btn.active { 
        background: linear-gradient(135deg, ${primaryColor} 0%, ${hoverColor} 100%); 
        color: ${bgBase}; 
        box-shadow: 0 4px 12px rgba(15, 220, 120, 0.3);
        font-weight: 600;
      }
      .nexva-mode-btn.active:hover {
        transform: scale(1.02);
      }
      
      .nexva-chat-messages { 
        flex: 1; 
        overflow-y: auto; 
        padding: 20px; 
        background: ${bgBase}; 
      }
      
      .nexva-chat-message { 
        margin-bottom: 16px; 
        display: flex; 
        gap: 10px; 
        align-items: flex-start; 
        animation: messageSlide 0.3s ease;
      }
      @keyframes messageSlide {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
      }
      .nexva-chat-message.user { 
        flex-direction: row-reverse; 
      }
      
      .nexva-chat-message-content { 
        max-width: 75%; 
        padding: 12px 16px; 
        border-radius: 12px; 
        font-size: 14px; 
        line-height: 1.5; 
        word-wrap: break-word; 
      }
      .nexva-chat-message.assistant .nexva-chat-message-content { 
        background: ${bgTertiary}; 
        color: ${textDefault}; 
        border-radius: 12px 12px 12px 2px;
      }
      .nexva-chat-message.user .nexva-chat-message-content { 
        background: linear-gradient(135deg, ${primaryColor} 0%, ${hoverColor} 100%); 
        color: ${bgBase}; 
        border-radius: 12px 12px 2px 12px; 
        font-weight: 500; 
        box-shadow: 0 4px 12px rgba(15, 220, 120, 0.2);
      }
      .nexva-chat-message.system .nexva-chat-message-content { 
        background: ${bgOverlay}; 
        color: ${textSecondary}; 
        text-align: center; 
        max-width: 100%; 
        font-size: 13px;
        border-radius: 8px;
        padding: 8px 12px;
      }
      
      .nexva-chat-message.human { 
        align-items: flex-start; 
      }
      .nexva-human-avatar { 
        width: 32px; 
        height: 32px; 
        min-width: 32px; 
        border-radius: 50%; 
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        color: white; 
      }
      .nexva-human-avatar svg { 
        width: 18px; 
        height: 18px; 
      }
      .nexva-human-message-wrapper { 
        flex: 1; 
        max-width: calc(100% - 42px); 
      }
      .nexva-human-name { 
        font-size: 11px; 
        font-weight: 600; 
        color: #8b5cf6; 
        margin-bottom: 4px; 
        letter-spacing: 0.3px; 
      }
      .nexva-chat-message.human .nexva-chat-message-content { 
        background: ${bgTertiary}; 
        color: ${textDefault}; 
        border-radius: 12px 12px 12px 2px; 
        border: 1px solid rgba(139, 92, 246, 0.2); 
        max-width: 100%; 
      }
      
      .nexva-load-more-indicator { 
        text-align: center; 
        padding: 10px; 
        font-size: 12px; 
        color: ${textSecondary}; 
        background: ${bgOverlay}; 
        border-radius: 8px; 
        margin-bottom: 12px; 
      }
      
      .nexva-p { margin: 8px 0; line-height: 1.6; }
      .nexva-p:first-child { margin-top: 0; }
      .nexva-p:last-child { margin-bottom: 0; }
      .nexva-h1, .nexva-h2, .nexva-h3 { margin: 16px 0 8px; font-weight: 600; line-height: 1.3; }
      .nexva-h1 { font-size: 1.5em; }
      .nexva-h2 { font-size: 1.3em; }
      .nexva-h3 { font-size: 1.1em; }
      .nexva-ul { margin: 8px 0; padding-left: 24px; }
      .nexva-li { margin: 4px 0; }
      .nexva-link { color: ${primaryColor}; text-decoration: underline; }
      .nexva-link:hover { color: ${hoverColor}; }
      .nexva-inline-code { background: ${bgOverlay}; padding: 2px 6px; border-radius: 4px; font-family: 'SF Mono', 'Monaco', monospace; font-size: 0.9em; }
      .nexva-code-block { margin: 12px 0; border-radius: 8px; overflow: hidden; background: ${bgBase}; border: 1px solid ${borderColor}; }
      .nexva-code-header { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: ${bgOverlay}; border-bottom: 1px solid ${borderColor}; }
      .nexva-code-lang { font-size: 12px; color: ${textSecondary}; text-transform: uppercase; font-weight: 500; }
      .nexva-code-copy { padding: 4px 12px; background: ${primaryColor}; color: ${bgBase}; border: none; border-radius: 4px; font-size: 11px; cursor: pointer; transition: all 0.2s; }
      .nexva-code-copy:hover { background: ${hoverColor}; }
      .nexva-code-pre { margin: 0; padding: 12px; overflow-x: auto; }
      .nexva-code-content { font-family: 'SF Mono', 'Monaco', monospace; font-size: 13px; line-height: 1.5; color: ${textDefault}; }
      
      .nexva-chat-input-area { 
        padding: 16px; 
        background: ${bgSecondary}; 
        border-top: 1px solid ${borderColor}; 
      }
      
      .nexva-chat-actions { 
        display: flex; 
        gap: 8px; 
        margin-bottom: 12px; 
      }
      .nexva-chat-action-btn { 
        flex: 1; 
        padding: 10px 14px; 
        border: 1px solid ${primaryColor}; 
        background: transparent; 
        color: ${primaryColor}; 
        border-radius: 8px; 
        font-size: 13px; 
        font-weight: 500; 
        cursor: pointer; 
        transition: all 0.2s; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        gap: 8px; 
      }
      .nexva-chat-action-btn:hover { 
        background: ${primaryColor}; 
        color: ${bgBase}; 
      }
      .nexva-chat-action-btn svg { 
        width: 16px; 
        height: 16px; 
        fill: currentColor; 
      }
      
      .nexva-chat-input-row { 
        display: flex; 
        gap: 10px; 
        align-items: center; 
      }
      
      .nexva-chat-voice-btn { 
        width: 42px; 
        height: 42px; 
        min-width: 42px; 
        border: none; 
        border-radius: 10px; 
        background: ${bgTertiary}; 
        color: ${textSecondary}; 
        cursor: pointer; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
      }
      .nexva-chat-voice-btn:hover { 
        background: linear-gradient(135deg, ${primaryColor} 0%, ${hoverColor} 100%); 
        color: ${bgBase}; 
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(15, 220, 120, 0.3);
      }
      .nexva-chat-voice-btn:active {
        transform: translateY(0);
      }
      .nexva-chat-voice-btn[data-voice-active="true"] { 
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); 
        color: white; 
        animation: voicePulse 2s cubic-bezier(0.4, 0, 0.2, 1) infinite;
        box-shadow: 0 4px 16px rgba(239, 68, 68, 0.4);
      }
      .nexva-chat-voice-btn[data-voice-active="true"]:hover {
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
        box-shadow: 0 6px 20px rgba(239, 68, 68, 0.5);
      }
      @keyframes voicePulse { 
        0%, 100% { box-shadow: 0 4px 16px rgba(239, 68, 68, 0.4), 0 0 0 0 rgba(239, 68, 68, 0.7); } 
        50% { box-shadow: 0 4px 16px rgba(239, 68, 68, 0.4), 0 0 0 6px rgba(239, 68, 68, 0); } 
      }
      .nexva-chat-voice-btn svg { 
        width: 20px; 
        height: 20px; 
      }
      
      .nexva-chat-input { 
        flex: 1; 
        padding: 11px 14px; 
        border: 1px solid ${borderColor}; 
        border-radius: 10px; 
        font-size: 14px; 
        outline: none; 
        background: ${bgBase}; 
        color: ${textDefault}; 
        transition: all 0.2s ease; 
        font-family: inherit;
      }
      .nexva-chat-input:focus { 
        background: ${bgBase}; 
        border-color: ${primaryColor}; 
        box-shadow: 0 0 0 3px rgba(15, 220, 120, 0.1); 
      }
      .nexva-chat-input:disabled { 
        opacity: 0.5; 
        cursor: not-allowed; 
      }
      .nexva-chat-input::placeholder { 
        color: ${textSecondary}; 
      }
      
      .nexva-chat-btn { 
        width: 42px; 
        height: 42px; 
        min-width: 42px; 
        border: none; 
        border-radius: 10px; 
        background: linear-gradient(135deg, ${primaryColor} 0%, ${hoverColor} 100%); 
        color: ${bgBase}; 
        cursor: pointer; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
        box-shadow: 0 4px 12px rgba(15, 220, 120, 0.3);
      }
      .nexva-chat-btn:hover { 
        background: linear-gradient(135deg, ${hoverColor} 0%, ${primaryColor} 100%); 
        transform: translateY(-2px); 
        box-shadow: 0 6px 16px rgba(15, 220, 120, 0.4); 
      }
      .nexva-chat-btn:active {
        transform: translateY(0);
      }
      .nexva-chat-btn:disabled { 
        background: ${bgOverlay}; 
        color: ${textSecondary}; 
        cursor: not-allowed; 
        transform: none; 
        box-shadow: none;
      }
      .nexva-chat-btn svg { 
        width: 20px; 
        height: 20px; 
        fill: currentColor; 
      }
      
      .nexva-chat-typing { 
        display: inline-flex; 
        gap: 5px; 
        padding: 12px 16px; 
        background: ${bgTertiary}; 
        border-radius: 12px 12px 12px 2px;
        border: 1px solid ${borderColor};
      }
      .nexva-chat-typing span { 
        width: 8px; 
        height: 8px; 
        background: ${primaryColor}; 
        border-radius: 50%; 
        animation: typing 1.4s infinite; 
      }
      .nexva-chat-typing span:nth-child(2) { 
        animation-delay: 0.2s; 
      }
      .nexva-chat-typing span:nth-child(3) { 
        animation-delay: 0.4s; 
      }
      @keyframes typing { 
        0%, 60%, 100% { transform: translateY(0); opacity: 0.4; } 
        30% { transform: translateY(-8px); opacity: 1; } 
      }
      
      .nexva-chat-voice-indicator { 
        position: fixed; 
        bottom: 110px; 
        ${position.includes('right') ? 'right: 110px;' : 'left: 110px;'} 
        background: ${bgSecondary}; 
        color: ${textDefault}; 
        padding: 14px 24px; 
        border-radius: 12px; 
        font-size: 14px; 
        font-weight: 500; 
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3); 
        display: none; 
        align-items: center; 
        gap: 12px; 
        border: 1px solid ${borderColor};
      }
      .nexva-chat-voice-indicator.active { 
        display: flex; 
      }
      .nexva-chat-voice-wave { 
        display: flex; 
        gap: 4px; 
      }
      .nexva-chat-voice-wave span { 
        width: 3px; 
        height: 18px; 
        background: ${primaryColor}; 
        border-radius: 2px; 
        animation: wave 1s infinite; 
      }
      .nexva-chat-voice-wave span:nth-child(2) { 
        animation-delay: 0.1s; 
      }
      .nexva-chat-voice-wave span:nth-child(3) { 
        animation-delay: 0.2s; 
      }
      .nexva-chat-voice-wave span:nth-child(4) { 
        animation-delay: 0.3s; 
      }
      @keyframes wave { 
        0%, 100% { height: 18px; } 
        50% { height: 8px; } 
      }
      
      @media (max-width: 480px) { 
        .nexva-chat-window { 
          width: calc(100vw - 24px); 
          height: calc(100vh - 110px); 
          right: 12px !important;
          left: 12px !important;
          bottom: 80px !important;
        } 
        .nexva-chat-container { 
          bottom: 12px !important; 
          right: 12px !important; 
          left: auto !important;
        }
        .nexva-chat-window.docked {
          width: 100vw;
          right: 0 !important;
          left: 0 !important;
        }
      }
      
      .nexva-chat-messages::-webkit-scrollbar { 
        width: 6px; 
      }
      .nexva-chat-messages::-webkit-scrollbar-track { 
        background: transparent; 
      }
      .nexva-chat-messages::-webkit-scrollbar-thumb { 
        background: ${borderColor}; 
        border-radius: 3px; 
      }
      .nexva-chat-messages::-webkit-scrollbar-thumb:hover { 
        background: rgba(255, 255, 255, 0.15); 
      }
    `;
    document.head.appendChild(style);
  }
};
import { Utils } from './utils.js';

export const Messaging = {
  isLoadingMore: false,
  hasMoreMessages: true,
  currentConversationId: null,
  apiUrl: null,
  
  init: function(conversationId, apiUrl) {
    this.currentConversationId = conversationId;
    this.apiUrl = apiUrl;
    this.attachScrollListener();
  },
  
  attachScrollListener: function() {
    const container = document.getElementById('nexvaChatMessages');
    if (!container) return;
    
    container.addEventListener('scroll', async () => {
      if (this.isLoadingMore || !this.hasMoreMessages || !this.currentConversationId) return;
      
      if (container.scrollTop < 50) {
        await this.loadMoreMessages();
      }
    });
  },
  
  async loadMoreMessages() {
    if (this.isLoadingMore || !this.hasMoreMessages) return;
    
    const container = document.getElementById('nexvaChatMessages');
    const firstMessage = container.querySelector('.nexva-chat-message[data-message-id]');
    if (!firstMessage) return;
    
    const beforeMessageId = firstMessage.dataset.messageId;
    const oldScrollHeight = container.scrollHeight;
    
    this.isLoadingMore = true;
    this.showLoadingIndicator();
    
    try {
      const response = await fetch(
        `${this.apiUrl}/api/conversations/${this.currentConversationId}/messages?limit=10&before_message_id=${beforeMessageId}`
      );
      
      if (!response.ok) throw new Error('Failed to load messages');
      
      const messages = await response.json();
      
      if (messages.length === 0) {
        this.hasMoreMessages = false;
      } else {
        this.prependMessages(messages);
        const newScrollHeight = container.scrollHeight;
        container.scrollTop = newScrollHeight - oldScrollHeight;
      }
    } catch (error) {
      console.error('Error loading messages:', error);
    } finally {
      this.hideLoadingIndicator();
      this.isLoadingMore = false;
    }
  },
  
  prependMessages: function(messages) {
    const container = document.getElementById('nexvaChatMessages');
    const fragment = document.createDocumentFragment();
    
    messages.forEach(msg => {
      const messageDiv = document.createElement('div');
      messageDiv.className = 'nexva-chat-message ' + msg.role;
      messageDiv.dataset.messageId = msg.id;
      
      if (msg.sender_type === 'support') {
        messageDiv.classList.add('human');
        const agentName = msg.sender_email ? msg.sender_email.split('@')[0] : 'Support';
        messageDiv.innerHTML = `
          <div class="nexva-human-avatar">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
            </svg>
          </div>
          <div class="nexva-human-message-wrapper">
            <div class="nexva-human-name">${agentName}</div>
            <div class="nexva-chat-message-content">${this.formatMarkdown(msg.content)}</div>
          </div>
        `;
      } else if (msg.role === 'assistant') {
        messageDiv.innerHTML = '<div class="nexva-chat-message-content">' + this.formatMarkdown(msg.content) + '</div>';
      } else {
        messageDiv.innerHTML = '<div class="nexva-chat-message-content">' + Utils.escapeHtml(msg.content) + '</div>';
      }
      
      fragment.appendChild(messageDiv);
    });
    
    const firstChild = container.firstChild;
    container.insertBefore(fragment, firstChild);
  },
  
  showLoadingIndicator: function() {
    const container = document.getElementById('nexvaChatMessages');
    const indicator = document.createElement('div');
    indicator.id = 'nexvaLoadMoreIndicator';
    indicator.className = 'nexva-load-more-indicator';
    indicator.textContent = 'Loading...';
    container.insertBefore(indicator, container.firstChild);
  },
  
  hideLoadingIndicator: function() {
    const indicator = document.getElementById('nexvaLoadMoreIndicator');
    if (indicator) indicator.remove();
  },
  
  clearMessages: function() {
    const container = document.getElementById('nexvaChatMessages');
    container.innerHTML = '';
    this.hasMoreMessages = true;
  },
  
  addMessage: function(role, content, messageId = null) {
    const container = document.getElementById('nexvaChatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'nexva-chat-message ' + role;
    if (messageId) {
      messageDiv.dataset.messageId = messageId;
    }
    
    if (role === 'assistant') {
      messageDiv.innerHTML = '<div class="nexva-chat-message-content">' + this.formatMarkdown(content) + '</div>';
    } else {
      messageDiv.innerHTML = '<div class="nexva-chat-message-content">' + Utils.escapeHtml(content) + '</div>';
    }
    
    container.appendChild(messageDiv);
    this.scrollToBottom();
    return { role, content };
  },
  
  addHumanMessage: function(content, senderEmail, messageId = null) {
    const container = document.getElementById('nexvaChatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'nexva-chat-message assistant human';
    if (messageId) {
      messageDiv.dataset.messageId = messageId;
    }
    
    const agentName = senderEmail ? senderEmail.split('@')[0] : 'Support';
    
    messageDiv.innerHTML = `
      <div class="nexva-human-avatar">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
        </svg>
      </div>
      <div class="nexva-human-message-wrapper">
        <div class="nexva-human-name">${agentName}</div>
        <div class="nexva-chat-message-content">${this.formatMarkdown(content)}</div>
      </div>
    `;
    
    container.appendChild(messageDiv);
    this.scrollToBottom();
    return { role: 'assistant', content, sender_type: 'support' };
  },
  
  showTyping: function() {
    const container = document.getElementById('nexvaChatMessages');
    const typing = document.createElement('div');
    typing.className = 'nexva-chat-message assistant';
    typing.id = 'nexvaTyping';
    typing.innerHTML = '<div class="nexva-chat-typing"><span></span><span></span><span></span></div>';
    container.appendChild(typing);
    this.scrollToBottom();
  },
  
  hideTyping: function() {
    const typing = document.getElementById('nexvaTyping');
    if (typing) typing.remove();
  },
  
  appendToLastMessage: function(content) {
    this.hideTyping();
    const container = document.getElementById('nexvaChatMessages');
    let lastMessage = container.querySelector('.nexva-chat-message.assistant:last-child');
    
    if (!lastMessage || lastMessage.dataset.finalized === 'true') {
      lastMessage = document.createElement('div');
      lastMessage.className = 'nexva-chat-message assistant';
      lastMessage.innerHTML = '<div class="nexva-chat-message-content"></div>';
      lastMessage.dataset.rawContent = '';
      container.appendChild(lastMessage);
    }
    
    const contentDiv = lastMessage.querySelector('.nexva-chat-message-content');
    lastMessage.dataset.rawContent = (lastMessage.dataset.rawContent || '') + content;
    contentDiv.innerHTML = this.formatMarkdown(lastMessage.dataset.rawContent);
    this.scrollToBottom();
  },
  
  finalizeMessage: function() {
    const container = document.getElementById('nexvaChatMessages');
    const lastMessage = container.querySelector('.nexva-chat-message.assistant:last-child');
    if (lastMessage) {
      lastMessage.dataset.finalized = 'true';
      const contentDiv = lastMessage.querySelector('.nexva-chat-message-content');
      if (lastMessage.dataset.rawContent) {
        contentDiv.innerHTML = this.formatMarkdown(lastMessage.dataset.rawContent);
      }
    }
  },
  
  scrollToBottom: function() {
    const container = document.getElementById('nexvaChatMessages');
    container.scrollTop = container.scrollHeight;
  },
  
  formatMarkdown: function(text) {
    let html = Utils.escapeHtml(text);
    
    html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
      const language = lang || 'plaintext';
      const codeId = 'code-' + Math.random().toString(36).substr(2, 9);
      return `<div class="nexva-code-block">
        <div class="nexva-code-header">
          <span class="nexva-code-lang">${Utils.escapeHtml(language)}</span>
          <button class="nexva-code-copy" onclick="navigator.clipboard.writeText(document.getElementById('${codeId}').textContent).then(() => { const btn = event.target; btn.textContent = 'Copied!'; setTimeout(() => btn.textContent = 'Copy', 2000); })">Copy</button>
        </div>
        <pre class="nexva-code-pre"><code id="${codeId}" class="nexva-code-content">${code.trim()}</code></pre>
      </div>`;
    });
    
    html = html.replace(/`([^`]+)`/g, '<code class="nexva-inline-code">$1</code>');
    
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="nexva-link">$1</a>');
    
    html = html.replace(/(?<!["=])(https?:\/\/[^\s<>"]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer" class="nexva-link">$1</a>');
    
    html = html.replace(/^### (.+)$/gm, '<h3 class="nexva-h3">$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2 class="nexva-h2">$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1 class="nexva-h1">$1</h1>');
    
    html = html.replace(/^\* (.+)$/gm, '<li class="nexva-li">$1</li>');
    html = html.replace(/^- (.+)$/gm, '<li class="nexva-li">$1</li>');
    html = html.replace(/(<li class="nexva-li">.*<\/li>\n?)+/g, '<ul class="nexva-ul">$&</ul>');
    
    html = html.replace(/^\d+\. (.+)$/gm, '<li class="nexva-li">$1</li>');
    
    html = html.replace(/\n\n/g, '</p><p class="nexva-p">');
    html = '<p class="nexva-p">' + html + '</p>';
    
    html = html.replace(/<p class="nexva-p"><\/p>/g, '');
    html = html.replace(/<p class="nexva-p">(<div|<h[123]|<ul)/g, '$1');
    html = html.replace(/(<\/div>|<\/h[123]>|<\/ul>)<\/p>/g, '$1');
    
    return html;
  }
};

import { Messaging } from './messaging.js';
import { UI } from './ui.js';

export const VoiceChat = {
  recognition: null,
  isRecording: false,
  currentMessageIndex: -1,
  finalTranscript: '',
  silenceTimer: null,
  continuousMode: false,
  messageSent: false,
  originalHeaderTitle: '',
  isSpeaking: false,
  onInterrupt: null,
  interruptSent: false,
  isPaused: false,
  mediaStream: null,
  
  async requestMicrophoneAccess() {
    try {
      if (this.mediaStream) {
        return true;
      }
      
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      
      console.log('[VoiceChat] Microphone access granted with echo cancellation');
      return true;
    } catch (error) {
      console.error('[VoiceChat] Microphone access denied:', error);
      Messaging.addMessage('system', '❌ Microphone access denied. Please allow microphone access.');
      return false;
    }
  },
  
  pauseRecognition: function() {
    if (this.recognition && this.isRecording && !this.isPaused) {
      this.isPaused = true;
      try {
        this.recognition.stop();
      } catch (e) {
        console.log('[VoiceChat] Error pausing recognition:', e);
      }
    }
  },
  
  resumeRecognition: function() {
    if (this.isPaused && this.continuousMode) {
      this.isPaused = false;
      setTimeout(() => {
        if (!this.isRecording && this.continuousMode) {
          try {
            this.recognition.start();
          } catch (e) {
            console.log('[VoiceChat] Error resuming recognition:', e);
          }
        }
      }, 500);
    }
  },
  
  isSupported: function() {
    return ('webkitSpeechRecognition' in window) || ('SpeechRecognition' in window);
  },
  
  start: async function(onTranscript, continuous = false) {
    if (!this.isSupported()) {
      Messaging.addMessage('system', '❌ Voice input is not supported in your browser. Please use Chrome or Edge.');
      return false;
    }
    
    if (this.isRecording && this.recognition) {
      return true;
    }
    
    const hasAccess = await this.requestMicrophoneAccess();
    if (!hasAccess) {
      return false;
    }
    
    this.continuousMode = continuous;
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.recognition = new SpeechRecognition();
    this.recognition.continuous = true;
    this.recognition.interimResults = true;
    this.recognition.lang = 'en-US';
    this.recognition.maxAlternatives = 1;
    
    this.finalTranscript = '';
    this.currentMessageIndex = -1;
    this.messageSent = false;
    this.interruptSent = false;
    
    this.recognition.onstart = () => {
      this.isRecording = true;
      document.getElementById('nexvaVoiceIndicator').classList.add('active');
      
      if (!this.originalHeaderTitle) {
        const titleElement = document.querySelector('.nexva-chat-header-title h3');
        if (titleElement) {
          this.originalHeaderTitle = titleElement.textContent;
        }
      }
      
      UI.animateHeaderTitle(true, this.originalHeaderTitle);
      this.setListeningEffect();
    };
    
    this.recognition.onresult = (event) => {
      if (this.isPaused) {
        console.log('[VoiceChat] Ignoring result - paused');
        return;
      }
      
      let interimTranscript = '';
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          this.finalTranscript += (this.finalTranscript ? ' ' : '') + transcript;
        } else {
          interimTranscript += transcript;
        }
      }
      
      const displayText = this.finalTranscript + (interimTranscript ? ' ' + interimTranscript : '');
      
      if (displayText.trim() && this.currentMessageIndex < 0) {
        const container = document.getElementById('nexvaChatMessages');
        Messaging.addMessage('user', '');
        const messages = container.querySelectorAll('.nexva-chat-message.user');
        this.currentMessageIndex = messages.length - 1;
      }
      
      this.updateUserMessage(displayText);
      
      if (displayText.trim()) {
        if (!this.isSpeaking) {
          this.isSpeaking = true;
          this.updateMicrophoneColor(true);
        }
        
        if (this.onInterrupt && !this.interruptSent) {
          this.interruptSent = true;
          this.onInterrupt();
        }
      }
      
      if (this.silenceTimer) clearTimeout(this.silenceTimer);
      
      if (displayText.trim() && !this.messageSent) {
        this.silenceTimer = setTimeout(() => {
          if (this.messageSent) return;
          
          const textToSend = (this.finalTranscript + (interimTranscript ? ' ' + interimTranscript : '')).trim();
          if (textToSend) {
            this.messageSent = true;
            this.updateUserMessage(textToSend);
            onTranscript(textToSend);
            this.finalTranscript = '';
            this.currentMessageIndex = -1;
            
            if (this.recognition) {
              this.recognition.stop();
            }
          }
        }, 2000);
      }
    };
    
    this.recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      if (event.error !== 'no-speech' && event.error !== 'aborted') {
        if (this.currentMessageIndex >= 0) {
          this.removeUserMessage();
        }
        Messaging.addMessage('system', '❌ Voice recognition error. Please try again.');
      }
      this.cleanup();
    };
    
    this.recognition.onend = () => {
      if (this.silenceTimer) {
        clearTimeout(this.silenceTimer);
        this.silenceTimer = null;
      }
      
      this.isRecording = false;
      this.finalTranscript = '';
      this.currentMessageIndex = -1;
      this.messageSent = false;
      this.isSpeaking = false;
      
      this.updateMicrophoneColor(false);
      
      const indicator = document.getElementById('nexvaVoiceIndicator');
      if (indicator) {
        indicator.classList.remove('active');
      }
      
      UI.animateHeaderTitle(false, this.originalHeaderTitle);
    };
    
    this.recognition.start();
    return true;
  },
  
  updateUserMessage: function(content) {
    if (this.currentMessageIndex < 0) return;
    
    const container = document.getElementById('nexvaChatMessages');
    const messages = container.querySelectorAll('.nexva-chat-message.user');
    const targetMessage = messages[this.currentMessageIndex];
    
    if (targetMessage) {
      const contentDiv = targetMessage.querySelector('.nexva-chat-message-content');
      if (contentDiv) {
        contentDiv.textContent = content;
      }
    }
    
    Messaging.scrollToBottom();
  },
  
  removeUserMessage: function() {
    if (this.currentMessageIndex < 0) return;
    
    const container = document.getElementById('nexvaChatMessages');
    const messages = container.querySelectorAll('.nexva-chat-message.user');
    const targetMessage = messages[this.currentMessageIndex];
    
    if (targetMessage) {
      targetMessage.remove();
    }
  },
  
  updateMicrophoneColor: function(isSpeaking) {
    const voicePromptBtn = document.getElementById('nexvaVoicePrompt');
    const voiceToggleBtn = document.getElementById('nexvaVoiceToggle');
    
    if (isSpeaking) {
      if (voicePromptBtn) {
        voicePromptBtn.style.background = '#ef4444';
        voicePromptBtn.style.transform = 'scale(1.1)';
        voicePromptBtn.style.boxShadow = '0 0 0 0 rgba(239, 68, 68, 1)';
        voicePromptBtn.style.animation = 'pulse 1s infinite';
      }
      if (voiceToggleBtn) {
        voiceToggleBtn.style.background = '#ef4444';
        voiceToggleBtn.style.transform = 'scale(1.1)';
        voiceToggleBtn.style.boxShadow = '0 0 0 0 rgba(239, 68, 68, 1)';
        voiceToggleBtn.style.animation = 'pulse 1s infinite';
      }
    } else {
      if (voicePromptBtn) {
        voicePromptBtn.style.background = '';
        voicePromptBtn.style.transform = '';
        voicePromptBtn.style.boxShadow = '';
        voicePromptBtn.style.animation = '';
      }
      if (voiceToggleBtn) {
        voiceToggleBtn.style.background = '';
        voiceToggleBtn.style.transform = '';
        voiceToggleBtn.style.boxShadow = '';
        voiceToggleBtn.style.animation = '';
      }
    }
  },
  
  setListeningEffect: function() {
    const voicePromptBtn = document.getElementById('nexvaVoicePrompt');
    const voiceToggleBtn = document.getElementById('nexvaVoiceToggle');
    
    if (voicePromptBtn && voicePromptBtn.classList.contains('recording')) {
      voicePromptBtn.style.animation = 'subtlePulse 2s infinite';
      voicePromptBtn.style.boxShadow = '0 0 0 rgba(79, 70, 229, 0.4)';
    }
    if (voiceToggleBtn && voiceToggleBtn.classList.contains('recording')) {
      voiceToggleBtn.style.animation = 'subtlePulse 2s infinite';
      voiceToggleBtn.style.boxShadow = '0 0 0 rgba(79, 70, 229, 0.4)';
    }
  },
  
  stop: function() {
    this.continuousMode = false;
    this.cleanup();
    if (this.currentMessageIndex >= 0) {
      this.removeUserMessage();
    }
  },
  
  cleanup: function() {
    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (e) {}
      this.recognition = null;
    }
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
      console.log('[VoiceChat] Microphone stream stopped');
    }
    if (this.silenceTimer) {
      clearTimeout(this.silenceTimer);
      this.silenceTimer = null;
    }
    this.isRecording = false;
    this.finalTranscript = '';
    this.currentMessageIndex = -1;
    this.messageSent = false;
    const indicator = document.getElementById('nexvaVoiceIndicator');
    if (indicator) {
      indicator.classList.remove('active');
    }
  }
};

import { Messaging } from './messaging.js';
import { Utils } from './utils.js';
import { VoiceChat } from './voice.js';

export const WebSocketManager = {
  ws: null,
  conversationId: null,
  onResponseComplete: null,
  audioQueue: [],
  isPlayingAudio: false,
  
  connect: function(config, onConversationUpdate, existingConversationId = null) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) return;
    
    const protocol = config.apiUrl.startsWith('https') ? 'wss:' : 'ws:';
    const host = config.apiUrl.replace(/^https?:\/\//, '');
    this.ws = new WebSocket(`${protocol}//${host}/ws/chat/${config.apiKey}`);
    
    if (existingConversationId) {
      this.conversationId = existingConversationId;
    }
    
    this.ws.onopen = () => {
      console.log('[WebSocket] Connected to server');
      const initMessage = {
        session_id: Utils.generateSessionId()
      };
      if (existingConversationId) {
        initMessage.conversation_id = existingConversationId;
        console.log('[WebSocket] Resuming conversation:', existingConversationId);
      }
      this.ws.send(JSON.stringify(initMessage));
    };
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'history') {
        Messaging.clearMessages();
        data.messages.forEach(msg => {
          if (msg.sender_type === 'support') {
            Messaging.addHumanMessage(msg.content, msg.sender_email, msg.id);
          } else {
            Messaging.addMessage(msg.role, msg.content, msg.id);
          }
        });
        if (onConversationUpdate && this.conversationId) {
          onConversationUpdate(this.conversationId, data.mode);
        }
      } else if (data.type === 'chunk') {
        Messaging.appendToLastMessage(data.text);
      } else if (data.type === 'complete') {
        Messaging.finalizeMessage();
        if (data.conversation_id) {
          this.conversationId = data.conversation_id;
          if (onConversationUpdate) {
            onConversationUpdate(data.conversation_id);
          }
        }
        if (this.onResponseComplete) {
          this.onResponseComplete();
        }
      } else if (data.type === 'human_message') {
        console.log('[WebSocket] ✅ Received human message:', data.content.substring(0, 50));
        Messaging.addHumanMessage(data.content, data.sender_email);
      } else if (data.type === 'ticket_resolved') {
        console.log('[WebSocket] Ticket resolved, switching to AI mode');
        Messaging.addMessage('system', '✅ ' + data.message);
        if (onConversationUpdate) {
          onConversationUpdate(this.conversationId, 'ai');
        }
      }
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      Messaging.addMessage('system', '❌ Connection error. Please try again.');
    };
    
    this.ws.onclose = () => console.log('WebSocket closed');
  },
  
  sendMessage: function(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ 
        message: message,
        session_id: Utils.generateSessionId()
      }));
      return true;
    }
    return false;
  },
  
  close: function() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  },
  
  queueAudio: function(audioBlob) {
    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    audio.setAttribute('sinkId', 'default');
    
    this.audioQueue.push({ audio, url: audioUrl });
    
    if (!this.isPlayingAudio) {
      this.playNextAudio();
    }
  },
  
  playNextAudio: function() {
    if (this.audioQueue.length === 0) {
      this.isPlayingAudio = false;
      this.currentAudio = null;
      this.updatePlaybackStatus(false);
      VoiceChat.resumeRecognition();
      return;
    }

    this.isPlayingAudio = true;
    this.updatePlaybackStatus(true);
    VoiceChat.pauseRecognition();
    VoiceChat.interruptSent = false;
    
    const audioData = this.audioQueue.shift();
    const audio = audioData.audio;
    const url = audioData.url;
    
    this.currentAudio = audio;
    
    audio.onended = () => {
      URL.revokeObjectURL(url);
      this.playNextAudio();
    };
    
    audio.onerror = () => {
      URL.revokeObjectURL(url);
      this.playNextAudio();
    };
    
    audio.play().catch(err => {
      console.error('Audio play failed:', err);
      URL.revokeObjectURL(url);
      this.playNextAudio();
    });
  },
  
  updatePlaybackStatus: function(isPlaying) {
    const voiceStatus = document.getElementById('nexvaVoiceStatus');
    if (voiceStatus) {
      if (isPlaying) {
        voiceStatus.innerHTML = '<span style="opacity: 0.8; font-size: 11px;">Start speaking to interrupt</span>';
        voiceStatus.style.color = '#0fdc78';
      } else {
        voiceStatus.textContent = 'Listening...';
        voiceStatus.style.color = '';
      }
    }
  },
  
  stopAllAudio: function() {
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio = null;
    }
    
    this.audioQueue.forEach(({audio, url}) => {
      audio.pause();
      URL.revokeObjectURL(url);
    });
    this.audioQueue = [];
    this.isPlayingAudio = false;
    this.updatePlaybackStatus(false);
    VoiceChat.resumeRecognition();
  }
};

import { Config } from './config.js';
import { Styles } from './styles.js';
import { UI } from './ui.js';
import { Messaging } from './messaging.js';
import { WebSocketManager } from './websocket.js';
import { VoiceChat } from './voice.js';
import { Utils } from './utils.js';

export const NexvaChat = {
  config: null,
  isOpen: false,
  supportRequested: false,
  initialized: false,
  conversationId: null,
  currentMode: 'ai',
  
  init: function(apiKey, options) {
    console.log('[Nexva] Initializing widget...', { apiKey, options });
    
    // Prevent double initialization
    if (this.initialized) {
      console.warn('[Nexva] Widget already initialized, skipping...');
      return;
    }
    
    // Remove any existing widget
    const existingContainer = document.querySelector('.nexva-chat-container');
    if (existingContainer) {
      console.log('[Nexva] Removing existing widget...');
      existingContainer.remove();
    }
    
    this.config = Config.init(apiKey, options);
    console.log('[Nexva] Config initialized:', this.config);
    Styles.inject(this.config);
    console.log('[Nexva] Styles injected');
    UI.createWidget(this.config);
    console.log('[Nexva] Widget created');
    this.attachEventListeners();
    console.log('[Nexva] Event listeners attached');
    
    this.initialized = true;
    
    if (this.config.autoOpen) {
      setTimeout(() => this.openChat(), 1000);
    }
    console.log('[Nexva] Widget initialization complete');
  },
  
  attachEventListeners: function() {
    const button = document.getElementById('nexvaChatButton');
    const closeBtn = document.getElementById('nexvaChatClose');
    const fullscreenBtn = document.getElementById('nexvaFullscreen');
    const dockBtn = document.getElementById('nexvaDock');
    const sendBtn = document.getElementById('nexvaChatSend');
    const input = document.getElementById('nexvaChatInput');
    const voiceBtn = document.getElementById('nexvaVoiceBtn');
    
    console.log('[Nexva] Attaching event listeners...');
    console.log('[Nexva] Button element:', button);
    
    if (button) {
      button.addEventListener('click', () => {
        console.log('[Nexva] Button clicked! Current isOpen:', this.isOpen);
        this.toggleChat();
      });
    } else {
      console.error('[Nexva] Chat button not found!');
    }
    
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.closeChat());
    }
    
    if (fullscreenBtn) {
      fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
    }
    
    if (dockBtn) {
      dockBtn.addEventListener('click', () => this.toggleDock());
    }
    
    if (sendBtn) {
      sendBtn.addEventListener('click', () => this.sendMessage());
    }
    
    if (input) {
      input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') this.sendMessage();
      });
    }
    
    if (voiceBtn) {
      voiceBtn.addEventListener('click', () => this.toggleVoiceMode());
    }
    
    document.querySelectorAll('.nexva-mode-btn').forEach(btn => {
      btn.addEventListener('click', () => this.switchMode(btn.dataset.mode));
    });
    
    console.log('[Nexva] Event listeners attached successfully');
  },
  
  voiceActive: false,
  
  toggleVoiceMode: function() {
    const voiceBtn = document.getElementById('nexvaVoiceBtn');
    const input = document.getElementById('nexvaChatInput');
    
    if (this.voiceActive) {
      this.voiceActive = false;
      voiceBtn.dataset.voiceActive = 'false';
      voiceBtn.setAttribute('title', 'Click to start voice input');
      this.stopVoiceChat();
      if (input) input.disabled = false;
    } else {
      this.voiceActive = true;
      voiceBtn.dataset.voiceActive = 'true';
      voiceBtn.setAttribute('title', 'Click to stop voice input');
      if (input) input.disabled = true;
      this.startVoiceChat();
    }
  },
  
  startVoiceChat: function() {
    const voiceBtn = document.getElementById('nexvaVoiceBtn');
    
    this.voiceActive = true;
    if (voiceBtn) voiceBtn.classList.add('recording');
    
    const protocol = this.config.apiUrl.startsWith('https') ? 'wss:' : 'ws:';
    const host = this.config.apiUrl.replace(/^https?:\/\//, '');
    this.voiceChatWs = new WebSocket(`${protocol}//${host}/ws/voice-chat/${this.config.apiKey}`);
    
    let isSending = false;
    
    this.voiceChatWs.onopen = () => {
      WebSocketManager.onResponseComplete = () => {
        if (this.voiceActive && VoiceChat.continuousMode) {
          setTimeout(() => {
            VoiceChat.start((transcript) => {
              if (this.voiceChatWs.readyState === WebSocket.OPEN && !isSending) {
                isSending = true;
                Messaging.showTyping();
                this.voiceChatWs.send(JSON.stringify({
                  type: "text_query",
                  text: transcript
                }));
              }
            }, true);
          }, 500);
        }
      };
      
      VoiceChat.onInterrupt = () => {
        if (this.voiceChatWs && this.voiceChatWs.readyState === WebSocket.OPEN) {
          this.voiceChatWs.send(JSON.stringify({ type: 'interrupt' }));
        }
        WebSocketManager.stopAllAudio();
        Messaging.hideTyping();
      };
      
      VoiceChat.start((transcript) => {
        if (this.voiceChatWs.readyState === WebSocket.OPEN && !isSending) {
          isSending = true;
          Messaging.showTyping();
          this.voiceChatWs.send(JSON.stringify({
            type: "text_query",
            text: transcript
          }));
        }
      }, true);
    };
    
    this.voiceChatWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === "response_start") {
        VoiceChat.interruptSent = false;
        VoiceChat.pauseRecognition();
      } else if (data.type === "text_chunk") {
        Messaging.appendToLastMessage(data.text);
      } else if (data.type === "audio_chunk") {
        const audioBlob = new Blob([Uint8Array.from(atob(data.audio), c => c.charCodeAt(0))], { type: 'audio/wav' });
        WebSocketManager.queueAudio(audioBlob);
      } else if (data.type === "response_end") {
        Messaging.finalizeMessage();
        isSending = false;
        if (this.voiceActive && WebSocketManager.onResponseComplete) {
          WebSocketManager.onResponseComplete();
        }
      } else if (data.type === "error") {
        Messaging.addMessage('system', `❌ ${data.message}`);
        Messaging.hideTyping();
        VoiceChat.resumeRecognition();
        isSending = false;
      }
    };
    
    this.voiceChatWs.onerror = () => {
      Messaging.addMessage('system', '❌ Voice chat connection error');
      this.stopVoiceChat();
    };
    
    this.voiceChatWs.onclose = () => {
      if (this.voiceActive) {
        this.stopVoiceChat();
      }
    };
  },
  
  
  stopVoiceChat: function() {
    const voiceBtn = document.getElementById('nexvaVoiceBtn');
    
    this.voiceActive = false;
    WebSocketManager.onResponseComplete = null;
    VoiceChat.onInterrupt = null;
    
    if (this.voiceChatWs && this.voiceChatWs.readyState === WebSocket.OPEN) {
      this.voiceChatWs.send(JSON.stringify({ type: "stop" }));
      this.voiceChatWs.close();
      this.voiceChatWs = null;
    }
    
    WebSocketManager.stopAllAudio();
    
    if (voiceBtn) {
      voiceBtn.classList.remove('recording');
      voiceBtn.dataset.voiceActive = 'false';
    }
    VoiceChat.stop();
  },
  
  toggleChat: function() {
    console.log('[Nexva] toggleChat called, isOpen:', this.isOpen);
    this.isOpen ? this.closeChat() : this.openChat();
  },
  
  openChat: function() {
    console.log('[Nexva] openChat called');
    this.isOpen = true;
    UI.toggleChat(true);
    
    const existingConversationId = Utils.getConversationId(this.config.apiKey);
    if (existingConversationId) {
      this.conversationId = existingConversationId;
      console.log('[Nexva] Resuming conversation:', existingConversationId);
    }
    
    WebSocketManager.connect(this.config, (convId, mode) => {
      if (convId) {
        this.conversationId = convId;
        Utils.saveConversationId(this.config.apiKey, convId);
        Messaging.init(convId, this.config.apiUrl);
      }
      if (mode) {
        this.currentMode = mode;
        UI.updateMode(mode);
      }
      this.updateActions();
    }, existingConversationId);
    
    this.updateActions();
    console.log('[Nexva] Chat opened, isOpen:', this.isOpen);
  },
  
  switchMode: function(mode) {
    console.log('[Nexva] switchMode called, mode:', mode, 'conversationId:', this.conversationId);
    
    if (!this.conversationId) {
      Messaging.addMessage('system', 'Let\'s start a conversation first');
      return;
    }
    
    if (mode === this.currentMode) {
      console.log('[Nexva] Already in mode:', mode);
      return;
    }
    
    const switchMessage = mode === 'human' 
      ? 'Connecting you to human support...'
      : 'Switching back to AI assistant...';
    
    Messaging.addMessage('system', switchMessage);
    
    console.log('[Nexva] Sending mode switch request to:', `${this.config.apiUrl}/api/conversations/${this.conversationId}/switch-mode`);
    
    fetch(`${this.config.apiUrl}/api/conversations/${this.conversationId}/switch-mode`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode })
    })
    .then(res => res.json())
    .then(data => {
      console.log('[Nexva] Mode switch response:', data);
      this.currentMode = mode;
      UI.updateMode(mode);
      const successMsg = mode === 'human'
        ? '👤 Connected to human support team'
        : '🤖 Now chatting with AI assistant';
      Messaging.addMessage('system', successMsg);
      this.updateActions();
    })
    .catch((error) => {
      console.error('[Nexva] Mode switch error:', error);
      Messaging.addMessage('system', '❌ Failed to switch mode. Please try again.');
    });
  },
  
  closeChat: function() {
    this.isOpen = false;
    UI.toggleChat(false);
    VoiceChat.stop();
  },
  
  toggleFullscreen: function() {
    UI.toggleFullscreen();
  },
  
  toggleDock: function() {
    UI.toggleDock();
  },
  
  sendMessage: function() {
    const input = document.getElementById('nexvaChatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    input.value = '';
    this.sendMessageText(message);
  },
  
  sendMessageText: function(message) {
    Messaging.addMessage('user', message);
    
    if (this.currentMode === 'ai') {
      Messaging.showTyping();
    }
    
    if (!WebSocketManager.sendMessage(message)) {
      Messaging.addMessage('system', '❌ Connection lost. Please reopen the chat.');
      Messaging.hideTyping();
    }
  },
  
  sendVoiceMessage: function(message) {
    if (this.currentMode === 'ai') {
      Messaging.showTyping();
    }
    
    if (!WebSocketManager.sendMessage(message)) {
      Messaging.addMessage('system', '❌ Connection lost. Please reopen the chat.');
      Messaging.hideTyping();
    }
  },
  
  updateActions: function() {
    UI.updateActions(
      this.config, 
      this.conversationId || WebSocketManager.conversationId, 
      this.supportRequested,
      () => this.requestSupport()
    );
  },
  
  requestSupport: function() {
    const convId = this.conversationId || WebSocketManager.conversationId;
    if (!convId) {
      Messaging.addMessage('system', '❌ No active conversation. Please send a message first.');
      return;
    }
    
    fetch(`${this.config.apiUrl}/api/conversations/${convId}/request-support`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    .then(res => {
      if (!res.ok) {
        if (res.status === 400) {
          return res.json().then(err => {
            throw new Error(err.detail || 'Support already requested');
          });
        }
        throw new Error('Failed to request support');
      }
      return res.json();
    })
    .then(data => {
      this.supportRequested = true;
      const message = data.message || 'Support requested';
      Messaging.addMessage('system', `✅ ${message}. A team member will assist you shortly.`);
      this.updateActions();
    })
    .catch((error) => {
      const errorMsg = error.message === 'Support already requested' 
        ? '⚠️ Support has already been requested for this conversation.'
        : '❌ Failed to request support. Please try again.';
      Messaging.addMessage('system', errorMsg);
    });
  }
};

