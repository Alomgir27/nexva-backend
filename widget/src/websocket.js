import { Messaging } from './messaging.js';
import { Utils } from './utils.js';
import { VoiceChat } from './voice.js';

export const WebSocketManager = {
  ws: null,
  conversationId: null,
  onResponseComplete: null,
  audioQueue: [],
  isPlayingAudio: false,
  sessionId: null,
  apiKey: null,
  onSupportMessage: null,
  config: null,
  onConversationUpdate: null,
  reconnectAttempts: 0,
  maxReconnectAttempts: 10,
  reconnectDelay: 2000,
  reconnectTimer: null,
  isManualClose: false,
  
  connect: function(config, onConversationUpdate, existingConversationId = null) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) return;
    
    this.config = config;
    this.onConversationUpdate = onConversationUpdate;
    this.apiKey = config.apiKey;
    this.sessionId = Utils.getOrCreateSessionId(config.apiKey);
    this.isManualClose = false;
    
    if (existingConversationId) {
      this.conversationId = existingConversationId;
    }
    
    const protocol = config.apiUrl.startsWith('https') ? 'wss:' : 'ws:';
    const host = config.apiUrl.replace(/^https?:\/\//, '');
    this.ws = new WebSocket(`${protocol}//${host}/ws/chat/${config.apiKey}`);
    
    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }
      
      const initMessage = {
        session_id: this.sessionId
      };
      if (this.conversationId) {
        initMessage.conversation_id = this.conversationId;
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
        VoiceChat.addAssistantTranscriptChunk(data.text);
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
        Messaging.addHumanMessage(data.content, data.sender_email);
        
        if (this.onSupportMessage) {
          this.onSupportMessage();
        }
      } else if (data.type === 'ticket_resolved') {
        Messaging.addMessage('system', '✅ ' + data.message);
        if (onConversationUpdate) {
          onConversationUpdate(this.conversationId, 'ai');
        }
      }
    };
    
    this.ws.onerror = (error) => {
      console.error('[WebSocket] Error:', error);
    };
    
    this.ws.onclose = () => {
      this.ws = null;
      
      if (!this.isManualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * this.reconnectAttempts;
        console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
        
        this.reconnectTimer = setTimeout(() => {
          if (this.config && this.apiKey) {
            this.connect(this.config, this.onConversationUpdate, this.conversationId);
          }
        }, delay);
      }
    };
  },
  
  sendMessage: function(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ 
        message: message,
        session_id: this.sessionId
      }));
      return true;
    }
    return false;
  },
  
  close: function() {
    this.isManualClose = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  },
  
  queueAudio: function(audioBlob) {
    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    const isAndroid = /android/i.test(navigator.userAgent);
    
    audio.preload = 'auto';
    if (isAndroid) {
      audio.volume = 1.0;
    }
    audio.load();
    
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
      if (this.onResponseComplete) {
        this.onResponseComplete();
      }
      return;
    }

    this.isPlayingAudio = true;
    this.updatePlaybackStatus(true);
    VoiceChat.interruptSent = false;
    
    const audioData = this.audioQueue.shift();
    const audio = audioData.audio;
    const url = audioData.url;
    this.currentAudio = audio;
    
    const isAndroid = /android/i.test(navigator.userAgent);
    
    const cleanupAndNext = () => {
      URL.revokeObjectURL(url);
      this.playNextAudio();
    };
    
    audio.onended = cleanupAndNext;
    audio.onerror = cleanupAndNext;
    
    const attemptPlay = () => {
      const minReadyState = isAndroid ? 4 : 3;
      const waitTime = isAndroid ? 500 : 300;
      
      if (audio.readyState >= minReadyState) {
        audio.play().catch(err => {
          console.warn('Audio playback error:', err);
          cleanupAndNext();
        });
      } else {
        audio.addEventListener('canplaythrough', () => {
          audio.play().catch(err => {
            console.warn('Audio playback error:', err);
            cleanupAndNext();
          });
        }, { once: true });
        
        setTimeout(() => {
          if (audio.readyState < minReadyState) {
            audio.play().catch(cleanupAndNext);
          }
        }, waitTime);
      }
    };
    
    if (isAndroid) {
      setTimeout(attemptPlay, 150);
    } else {
      attemptPlay();
    }
  },
  
  updatePlaybackStatus: function(isPlaying) {
    VoiceChat.setAssistantSpeaking(isPlaying);
    const voiceStatus = document.getElementById('nexvaVoiceStatus');
    const voiceToggleBtn = document.getElementById('nexvaVoiceToggle');
    const isVoiceChatActive = voiceToggleBtn && voiceToggleBtn.classList.contains('recording');
    
    if (voiceStatus && isVoiceChatActive) {
      if (isPlaying) {
        if (VoiceChat.isEdge) {
          voiceStatus.innerHTML = '<span style="opacity: 0.8; font-size: 11px;">Assistant speaking...</span>';
        } else {
          voiceStatus.innerHTML = '<span style="opacity: 0.8; font-size: 11px;">Start speaking to interrupt</span>';
        }
        voiceStatus.style.color = '#0fdc78';
      } else {
        voiceStatus.textContent = 'Listening...';
        voiceStatus.style.color = '';
      }
    }
  },
  
  stopAllAudio: function() {
    if (this.currentAudio) {
      try {
        this.currentAudio.pause();
      } catch (e) {}
      const currentSrc = this.currentAudio.src;
      this.currentAudio.src = '';
      if (currentSrc && currentSrc.startsWith('blob:')) {
        try {
          URL.revokeObjectURL(currentSrc);
        } catch (e) {}
      }
      this.currentAudio = null;
    }
    
    this.audioQueue.forEach(({audio, url}) => {
      try {
        audio.pause();
        audio.src = '';
      } catch (e) {}
      if (url && url.startsWith('blob:')) {
        try {
          URL.revokeObjectURL(url);
        } catch (err) {}
      }
    });
    this.audioQueue = [];
    this.isPlayingAudio = false;
    this.updatePlaybackStatus(false);
    VoiceChat.clearAssistantTranscript();
  }
};

