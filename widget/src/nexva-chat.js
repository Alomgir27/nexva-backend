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

  init: function (apiKey, options) {
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

  attachEventListeners: function () {
    const button = document.getElementById('nexvaChatButton');
    const closeBtn = document.getElementById('nexvaChatClose');
    const fullscreenBtn = document.getElementById('nexvaFullscreen');
    const dockBtn = document.getElementById('nexvaDock');
    const sendBtn = document.getElementById('nexvaChatSend');
    const input = document.getElementById('nexvaChatInput');
    const voiceBtn = document.getElementById('nexvaVoiceBtn');
    const newChatBtn = document.getElementById('nexvaNewChat');

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

    if (newChatBtn) {
      newChatBtn.addEventListener('click', () => this.resetChat());
    }

    const interruptBtn = document.getElementById('nexvaVoiceInterruptBtn');
    if (interruptBtn) {
      interruptBtn.addEventListener('click', (e) => {
        e.stopPropagation(); // Prevent bubbling
        console.log('[Nexva] Manual interruption triggered');
        WebSocketManager.stopAllAudio();
        // Force restart listening immediately
        if (this.voiceActive) {
          VoiceChat.stop(); // Stop current instance
          setTimeout(() => {
            // Re-trigger start with the same callback logic
            const handleTranscript = (transcript) => {
              if (this.voiceChatWs.readyState === WebSocket.OPEN) {
                WebSocketManager.stopAllAudio();
                Messaging.showTyping();
                this.voiceChatWs.send(JSON.stringify({
                  type: "text_query",
                  text: transcript
                }));
                setTimeout(() => {
                  if (this.voiceActive) VoiceChat.start(handleTranscript, true);
                }, 200);
              }
            };
            VoiceChat.start(handleTranscript, true);
          }, 100);
        }
      });
    }

    document.querySelectorAll('.nexva-mode-btn').forEach(btn => {
      btn.addEventListener('click', () => this.switchMode(btn.dataset.mode));
    });

    console.log('[Nexva] Event listeners attached successfully');
  },

  voiceActive: false,

  toggleVoiceMode: function () {
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

  startVoiceChat: function () {
    const voiceBtn = document.getElementById('nexvaVoiceBtn');

    this.voiceActive = true;
    if (voiceBtn) voiceBtn.classList.add('recording');

    const protocol = this.config.apiUrl.startsWith('https') ? 'wss:' : 'ws:';
    const host = this.config.apiUrl.replace(/^https?:\/\//, '');
    this.voiceChatWs = new WebSocket(`${protocol}//${host}/ws/voice-chat/${this.config.apiKey}`);

    let isSending = false;

    this.voiceChatWs.onopen = () => {
      const handleTranscript = (transcript) => {
        if (this.voiceChatWs.readyState === WebSocket.OPEN) {
          // If we are interrupting, stop any current audio
          WebSocketManager.stopAllAudio();

          isSending = true;
          Messaging.showTyping();
          this.voiceChatWs.send(JSON.stringify({
            type: "text_query",
            text: transcript
          }));

          // Restart listening immediately to allow further interruptions/commands
          setTimeout(() => {
            if (this.voiceActive) {
              VoiceChat.start(handleTranscript, true);
            }
          }, 200);
        }
      };

      WebSocketManager.onResponseComplete = () => {
        if (this.voiceActive && VoiceChat.continuousMode) {
          setTimeout(() => {
            VoiceChat.start(handleTranscript, true);
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

      VoiceChat.start(handleTranscript, true);
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


  stopVoiceChat: function () {
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

  toggleChat: function () {
    console.log('[Nexva] toggleChat called, isOpen:', this.isOpen);
    this.isOpen ? this.closeChat() : this.openChat();
  },

  openChat: function () {
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

  switchMode: function (mode) {
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

  resetChat: function () {
    console.log('[Nexva] Resetting chat...');

    if (this.voiceActive) {
      this.stopVoiceChat();
    }

    Messaging.clearMessages();
    this.conversationId = null;
    Utils.saveConversationId(this.config.apiKey, null);
    WebSocketManager.close();

    Messaging.addMessage('assistant', this.config.welcomeMessage);
    Messaging.addMessage('system', '✨ Started a new conversation');

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
    }, null);
  },

  closeChat: function () {
    this.isOpen = false;
    UI.toggleChat(false);
    VoiceChat.stop();
  },

  toggleFullscreen: function () {
    UI.toggleFullscreen();
  },

  toggleDock: function () {
    UI.toggleDock();
  },

  sendMessage: function () {
    const input = document.getElementById('nexvaChatInput');
    const message = input.value.trim();

    if (!message) return;

    input.value = '';
    this.sendMessageText(message);
  },

  sendMessageText: function (message) {
    Messaging.addMessage('user', message);

    if (this.currentMode === 'ai') {
      Messaging.showTyping();
    }

    if (!WebSocketManager.sendMessage(message)) {
      Messaging.addMessage('system', '❌ Connection lost. Please reopen the chat.');
      Messaging.hideTyping();
    }
  },

  sendVoiceMessage: function (message) {
    if (this.currentMode === 'ai') {
      Messaging.showTyping();
    }

    if (!WebSocketManager.sendMessage(message)) {
      Messaging.addMessage('system', '❌ Connection lost. Please reopen the chat.');
      Messaging.hideTyping();
    }
  },

  updateActions: function () {
    UI.updateActions(
      this.config,
      this.conversationId || WebSocketManager.conversationId,
      this.supportRequested,
      () => this.requestSupport()
    );
  },

  requestSupport: function () {
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
  },

  destroy: function () {
    console.log('[Nexva] Destroying widget...');

    // Close any open connections
    if (this.voiceActive) {
      this.stopVoiceChat();
    }

    // Close the chat window
    this.closeChat();

    // Remove the widget container from DOM
    const container = document.querySelector('.nexva-chat-container');
    if (container) {
      container.remove();
    }

    // Reset state
    this.isOpen = false;
    this.supportRequested = false;
    this.initialized = false;
    this.conversationId = null;
    this.currentMode = 'ai';
    this.config = null;

    console.log('[Nexva] Widget destroyed');
  }
};

