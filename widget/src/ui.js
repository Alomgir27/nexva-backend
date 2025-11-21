export const UI = {
  isFullscreen: false,
  isDocked: false,
  fullscreenIcon: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/></svg>',
  fullscreenExitIcon: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/></svg>',
  dockIcon: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M21 3H3c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h18c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM3 19V5h11v14H3zm18 0h-5V5h5v14z"/></svg>',
  dockExitIcon: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 3h11v11H3zm7 2H5v7h5V5zm4 0v7h5V5h-5zM3 15h11v6H3zm7 2H5v2h5v-2zm4 0v2h5v-2h-5z"/></svg>',

  createWidget: function (config) {
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
            <button class="nexva-chat-icon-btn" id="nexvaNewChat" aria-label="New Chat" title="New Chat">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-2 10h-4v4h-2v-4H7v-2h4V7h2v4h4v2z"/></svg>
            </button>
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
        <span id="nexvaVoiceStatusText">Listening...</span>
        <button class="nexva-voice-interrupt-btn" id="nexvaVoiceInterruptBtn" title="Tap to Interrupt">
            <svg viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
                <path d="M6 6h12v12H6z" />
            </svg>
            Stop & Speak
        </button>
      </div>
    `;
    document.body.appendChild(container);
  },

  toggleChat: function (isOpen) {
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

  resetLayoutState: function () {
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

  toggleFullscreen: function () {
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

  toggleDock: function () {
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

  updateActions: function (config, conversationId, supportRequested, onRequestSupport) {
    if (!config.enableHumanSupport || !conversationId) {
      document.getElementById('nexvaChatActions').style.display = 'none';
      return;
    }

    const actionsDiv = document.getElementById('nexvaChatActions');
    actionsDiv.style.display = 'none';
  },

  updateMode: function (mode) {
    const buttons = document.querySelectorAll('.nexva-mode-btn');
    buttons.forEach(btn => {
      if (btn.dataset.mode === mode) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });
  },

  animateHeaderTitle: function (isListening, originalTitle) {
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
  },

  updateVoiceStatus: function (status) {
    const statusText = document.getElementById('nexvaVoiceStatusText');
    const interruptBtn = document.getElementById('nexvaVoiceInterruptBtn');
    const indicator = document.getElementById('nexvaVoiceIndicator');

    if (statusText) {
      if (status === 'speaking') {
        statusText.textContent = 'Speaking...';
        if (interruptBtn) interruptBtn.style.display = 'flex';
        if (indicator) indicator.classList.add('speaking');
      } else {
        statusText.textContent = 'Listening...';
        if (interruptBtn) interruptBtn.style.display = 'none';
        if (indicator) indicator.classList.remove('speaking');
      }
    }
  }
};

