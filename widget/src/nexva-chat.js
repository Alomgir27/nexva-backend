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
  hasReceivedSupportResponse: false,
  notificationAudio: null,
  
  init: function(apiKey, options) {
    // Prevent double initialization
    if (this.initialized) {
      return;
    }
    
    // Remove any existing widget
    const existingContainer = document.querySelector('.nexva-chat-container');
    if (existingContainer) {
      existingContainer.remove();
    }
    
    this.config = Config.init(apiKey, options);
    Styles.inject(this.config);
    UI.createWidget(this.config);
    this.attachEventListeners();
    
    // Initialize notification audio
    const audioPath = `${this.config.apiUrl}/notifications.wav`;
    this.notificationAudio = new Audio(audioPath);
    this.notificationAudio.volume = 1.0;
    
    this.initialized = true;
    
    if (this.config.autoOpen) {
      setTimeout(() => this.openChat(), 1000);
    }
  },
  
  attachEventListeners: function() {
    const button = document.getElementById('nexvaChatButton');
    const closeBtn = document.getElementById('nexvaChatClose');
    const fullscreenBtn = document.getElementById('nexvaFullscreen');
    const dockBtn = document.getElementById('nexvaDock');
    const sendBtn = document.getElementById('nexvaChatSend');
    const input = document.getElementById('nexvaChatInput');
    const voicePromptBtn = document.getElementById('nexvaVoicePrompt');
    const voiceToggleBtn = document.getElementById('nexvaVoiceToggle');
    
    if (button) {
      button.addEventListener('click', () => {
        this.toggleChat();
      });
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
    
    if (voicePromptBtn) {
      voicePromptBtn.addEventListener('click', () => this.toggleVoicePrompt());
    }
    
    if (voiceToggleBtn) {
      voiceToggleBtn.addEventListener('click', () => this.toggleVoiceChat());
    }
    
    document.querySelectorAll('.nexva-chat-tab').forEach(tab => {
      tab.addEventListener('click', () => this.switchTab(tab.dataset.tab));
    });
    
    const modeBtnAI = document.getElementById('nexvaModeBtnAI');
    const modeBtnHuman = document.getElementById('nexvaModeBtnHuman');
    if (modeBtnAI && modeBtnHuman && this.config.enableHumanSupport) {
      modeBtnAI.addEventListener('click', () => this.switchMode('ai'));
      modeBtnHuman.addEventListener('click', () => this.switchMode('human'));
    }
    
    // Preset questions click handlers
    document.querySelectorAll('.nexva-preset-question-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const question = btn.dataset.question;
        if (question) {
          const input = document.getElementById('nexvaChatInput');
          if (input) {
            input.value = question;
            this.sendMessage();
          }
          // Hide preset questions after first use
          const presetContainer = document.getElementById('nexvaPresetQuestions');
          if (presetContainer) {
            presetContainer.style.display = 'none';
          }
        }
      });
    });
  },
  
  switchTab: function(tab) {
    UI.switchTab(tab);
    if (tab === 'voice') {
      if (this.voicePromptActive) {
        this.voicePromptActive = false;
        WebSocketManager.onResponseComplete = null;
        VoiceChat.stop();
        const voicePromptBtn = document.getElementById('nexvaVoicePrompt');
        if (voicePromptBtn) voicePromptBtn.classList.remove('recording');
      }
    } else {
      this.stopVoiceChat();
    }
  },
  
  voicePromptActive: false,
  
  toggleVoicePrompt: function() {
    const voicePromptBtn = document.getElementById('nexvaVoicePrompt');
    if (this.voicePromptActive) {
      this.voicePromptActive = false;
      WebSocketManager.onResponseComplete = null;
      VoiceChat.stop();
      voicePromptBtn.classList.remove('recording');
    } else {
      this.voicePromptActive = true;
      voicePromptBtn.classList.add('recording');
      
      WebSocketManager.onResponseComplete = () => {
        if (this.voicePromptActive && VoiceChat.continuousMode) {
          setTimeout(() => {
            VoiceChat.start((transcript) => {
              this.sendVoiceMessage(transcript);
            }, true);
          }, 500);
        }
      };
      
      VoiceChat.start((transcript) => {
        this.sendVoiceMessage(transcript);
      }, true);
    }
  },
  
  voiceChatActive: false,
  
  toggleVoiceChat: function() {
    if (this.voiceChatActive) {
      this.stopVoiceChat();
    } else {
      this.startVoiceChat();
    }
  },
  
  startVoiceChat: function() {
    if (this.currentMode === 'human') {
      Messaging.addMessage('system', 'Voice chat is not available in human support mode. Please switch to AI mode first.');
      return;
    }
    
    const voiceToggleBtn = document.getElementById('nexvaVoiceToggle');
    const voiceStatus = document.getElementById('nexvaVoiceStatus');
    
    this.voiceChatActive = true;
    voiceToggleBtn.classList.add('recording');
    voiceStatus.textContent = 'Listening...';
    
    const protocol = this.config.apiUrl.startsWith('https') ? 'wss:' : 'ws:';
    const host = this.config.apiUrl.replace(/^https?:\/\//, '');
    this.voiceChatWs = new WebSocket(`${protocol}//${host}/ws/voice-chat/${this.config.apiKey}`);
    
    let isSending = false;
    const trySendTranscript = (rawTranscript) => {
      const transcript = (rawTranscript || '').trim();
      if (!transcript || !this.voiceChatWs || this.voiceChatWs.readyState !== WebSocket.OPEN || isSending) {
        return;
      }
      isSending = true;
      Messaging.showTyping();
      this.voiceChatWs.send(JSON.stringify({
        type: "text_query",
        text: transcript
      }));
    };
    
    this.voiceChatWs.onopen = () => {
      WebSocketManager.onResponseComplete = () => {
        if (this.voiceChatActive && VoiceChat.continuousMode) {
          setTimeout(() => {
            VoiceChat.start((transcript) => {
              trySendTranscript(transcript);
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
        Messaging.finalizeMessage();
        isSending = false;
      };
      
      VoiceChat.start((transcript) => {
        trySendTranscript(transcript);
      }, true);
    };
    
    this.voiceChatWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === "response_start") {
        VoiceChat.interruptSent = false;
        VoiceChat.clearAssistantTranscript();
      } else if (data.type === "text_chunk") {
        VoiceChat.addAssistantTranscriptChunk(data.text);
        Messaging.appendToLastMessage(data.text);
      } else if (data.type === "audio_chunk") {
        const audioBlob = new Blob([Uint8Array.from(atob(data.audio), c => c.charCodeAt(0))], { type: 'audio/wav' });
        WebSocketManager.queueAudio(audioBlob);
      } else if (data.type === "response_end") {
        Messaging.finalizeMessage();
        VoiceChat.clearAssistantTranscript();
        if (this.voiceChatActive && WebSocketManager.onResponseComplete) {
          isSending = false;
          WebSocketManager.onResponseComplete();
        } else {
          isSending = false;
        }
      } else if (data.type === "error") {
        Messaging.addMessage('system', `❌ ${data.message}`);
        Messaging.hideTyping();
        isSending = false;
      }
    };
    
    this.voiceChatWs.onerror = () => {
      Messaging.addMessage('system', '❌ Voice chat connection error');
      this.stopVoiceChat();
    };
    
    this.voiceChatWs.onclose = () => {
      if (this.voiceChatActive) {
        this.stopVoiceChat();
      }
    };
  },
  
  stopVoiceChat: function() {
    const voiceToggleBtn = document.getElementById('nexvaVoiceToggle');
    const voiceStatus = document.getElementById('nexvaVoiceStatus');
    
    this.voiceChatActive = false;
    WebSocketManager.onResponseComplete = null;
    VoiceChat.onInterrupt = null;
    
    if (this.voiceChatWs && this.voiceChatWs.readyState === WebSocket.OPEN) {
      this.voiceChatWs.send(JSON.stringify({ type: "stop" }));
      this.voiceChatWs.close();
      this.voiceChatWs = null;
    }
    
    WebSocketManager.stopAllAudio();
    
    if (voiceToggleBtn) {
      voiceToggleBtn.classList.remove('recording');
    }
    if (voiceStatus) {
      voiceStatus.textContent = 'Click microphone to start';
    }
    VoiceChat.stop();
  },
  
  toggleChat: function() {
    this.isOpen ? this.closeChat() : this.openChat();
  },
  
  openChat: function() {
    this.isOpen = true;
    this.hideNotification();
    UI.toggleChat(true);
    
    const existingConversationId = Utils.getConversationId(this.config.apiKey);
    if (existingConversationId) {
      this.conversationId = existingConversationId;
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
    
    WebSocketManager.onSupportMessage = () => {
      if (!this.hasReceivedSupportResponse) {
        this.hasReceivedSupportResponse = true;
        this.showNotification();
      }
    };
    
    this.updateActions();
  },
  
  switchMode: function(mode) {
    // Check if human support is enabled
    if (!this.config.enableHumanSupport) {
      return;
    }
    
    if (mode === this.currentMode) {
      return;
    }
    
    // If no conversation yet, just update the UI
    if (!this.conversationId) {
      this.currentMode = mode;
      UI.updateMode(mode);
      return;
    }
    
    const switchMessage = mode === 'human' 
      ? 'Connecting you to human support...'
      : 'Switching back to AI assistant...';
    
    Messaging.addMessage('system', switchMessage);
    
    fetch(`${this.config.apiUrl}/api/conversations/${this.conversationId}/switch-mode`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode })
    })
    .then(res => res.json())
    .then(data => {
      this.currentMode = mode;
      UI.updateMode(mode);
      const successMsg = mode === 'human'
        ? '👤 Connected to human support team'
        : '🤖 Now chatting with AI assistant';
      Messaging.addMessage('system', successMsg);
      this.updateActions();
    })
    .catch((error) => {
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
      this.hasReceivedSupportResponse = false;
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
  
  showNotification: function() {
    if (!this.isOpen) {
      UI.showNotificationBubble();
      this.playNotificationSound();
    }
  },
  
  hideNotification: function() {
    UI.hideNotificationBubble();
  },
  
  playNotificationSound: function() {
    if (this.notificationAudio) {
      this.notificationAudio.currentTime = 0;
      this.notificationAudio.play().catch(() => {});
    }
  }
};

