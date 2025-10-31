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
      return;
    }

    this.isPlayingAudio = true;
    this.updatePlaybackStatus(true);
    
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
  }
};

