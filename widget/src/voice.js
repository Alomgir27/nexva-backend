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
  assistantSpeaking: false,
  pendingTranscript: '',
  assistantTranscript: '',
  
  isSupported: function() {
    return ('webkitSpeechRecognition' in window) || ('SpeechRecognition' in window);
  },
  
  start: function(onTranscript, continuous = false) {
    if (!this.isSupported()) {
      Messaging.addMessage('system', '❌ Voice input is not supported in your browser. Please use Chrome or Edge.');
      return false;
    }
    
    if (this.isRecording && this.recognition) {
      return true;
    }
    
    this.continuousMode = continuous;
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.recognition = new SpeechRecognition();
    this.recognition.continuous = true;
    this.recognition.interimResults = true;
    this.recognition.lang = 'en-US';
    
    this.finalTranscript = '';
    this.pendingTranscript = '';
    this.assistantTranscript = '';
    this.currentMessageIndex = -1;
    this.messageSent = false;
    this.interruptSent = false;
    
    const flushTranscript = () => {
      if (this.messageSent) return;
      const textToSend = this.pendingTranscript.trim();
      if (!textToSend) return;
      this.messageSent = true;
      if (this.currentMessageIndex >= 0) {
        this.updateUserMessage(textToSend);
      }
      onTranscript(textToSend);
      this.pendingTranscript = '';
      this.finalTranscript = '';
      if (this.recognition) {
        try {
          this.recognition.stop();
        } catch (e) {}
      }
    };

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
      const trimmedText = displayText.trim();

      if (this.assistantSpeaking) {
        const lowerText = trimmedText.toLowerCase();
        const lowerAssistant = this.assistantTranscript.toLowerCase();
        if (lowerText && lowerAssistant && lowerAssistant.includes(lowerText)) {
          this.pendingTranscript = '';
          if (this.silenceTimer) {
            clearTimeout(this.silenceTimer);
            this.silenceTimer = null;
          }
          return;
        }
      }

      this.pendingTranscript = trimmedText;

      if (trimmedText && this.currentMessageIndex < 0) {
        const container = document.getElementById('nexvaChatMessages');
        Messaging.addMessage('user', '');
        const messages = container.querySelectorAll('.nexva-chat-message.user');
        this.currentMessageIndex = messages.length - 1;
      }
      
      this.updateUserMessage(displayText);
      
      if (trimmedText) {
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
      
      if (trimmedText && !this.messageSent) {
        this.silenceTimer = setTimeout(() => {
          flushTranscript();
        }, 2000);
      }
    };
    
    this.recognition.onerror = (event) => {
      if (event.error === 'no-speech' || event.error === 'aborted') {
        return;
      }
      if (this.currentMessageIndex >= 0) {
        this.removeUserMessage();
      }
      Messaging.addMessage('system', '❌ Voice recognition error. Please try again.');
      this.cleanup();
    };
    
    this.recognition.onend = () => {
      if (this.silenceTimer) {
        clearTimeout(this.silenceTimer);
        this.silenceTimer = null;
      }
      
      if (!this.messageSent) {
        flushTranscript();
      }

      this.isRecording = false;
      this.finalTranscript = '';
      this.pendingTranscript = '';
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
  
  setAssistantSpeaking: function(isSpeaking) {
    this.assistantSpeaking = isSpeaking;
    if (isSpeaking) {
      this.interruptSent = false;
    } else {
      this.clearAssistantTranscript();
    }
  },
  
  addAssistantTranscriptChunk: function(text) {
    if (!text) return;
    this.assistantTranscript = (this.assistantTranscript + text).slice(-500);
  },
  
  clearAssistantTranscript: function() {
    this.assistantTranscript = '';
  },
  
  stop: function() {
    this.continuousMode = false;
    if (this.currentMessageIndex >= 0) {
      this.removeUserMessage();
    }
    this.cleanup();
  },
  
  cleanup: function() {
    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (e) {}
      this.recognition = null;
    }
    if (this.silenceTimer) {
      clearTimeout(this.silenceTimer);
      this.silenceTimer = null;
    }
    this.isRecording = false;
    this.finalTranscript = '';
    this.pendingTranscript = '';
    this.assistantTranscript = '';
    this.currentMessageIndex = -1;
    this.messageSent = false;
    this.assistantSpeaking = false;
    const indicator = document.getElementById('nexvaVoiceIndicator');
    if (indicator) {
      indicator.classList.remove('active');
    }
  }
};

