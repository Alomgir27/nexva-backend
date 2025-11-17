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

