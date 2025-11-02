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
  micStream: null,
  onTranscriptCallback: null,
  isEdge: /Edg\//.test(navigator.userAgent),
  introAudio: null,
  introSoundPlayed: false,
  restartAttempts: 0,
  maxRestartAttempts: 5,
  lastRestartTime: 0,
  
  isSupported: function() {
    return ('webkitSpeechRecognition' in window) || ('SpeechRecognition' in window);
  },
  
  start: async function(onTranscript, continuous = false, playIntro = false) {
    if (!this.isSupported()) {
      Messaging.addMessage('system', '❌ Voice input is not supported in your browser. Please use Chrome or Edge.');
      return false;
    }
    
    if (this.isRecording && this.recognition) {
      return true;
    }
    
    this.continuousMode = continuous;
    this.onTranscriptCallback = onTranscript;
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      Messaging.addMessage('system', '❌ Speech recognition not supported in this browser. Please use Chrome, Safari, or Edge.');
      return false;
    }
    
    this.recognition = new SpeechRecognition();
    this.recognition.continuous = true;
    this.recognition.interimResults = true;
    this.recognition.lang = 'en-US';
    this.recognition.maxAlternatives = 1;
    
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
      const indicator = document.getElementById('nexvaVoiceIndicator');
      if (indicator) {
        indicator.classList.add('active');
      }
      
      const voiceStatus = document.getElementById('nexvaVoiceStatus');
      if (voiceStatus && voiceStatus.textContent === 'Loading...') {
        voiceStatus.textContent = 'Listening...';
        voiceStatus.style.color = '';
      }
      
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

      if (this.assistantSpeaking && trimmedText) {
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
        
        if (this.onInterrupt && !this.interruptSent) {
          this.interruptSent = true;
          this.onInterrupt();
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
      
      if (event.error === 'not-allowed') {
        Messaging.addMessage('system', '❌ Microphone access denied. Please allow microphone access.');
        this.cleanup();
        return;
      }
      
      if (this.currentMessageIndex >= 0) {
        this.removeUserMessage();
      }
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
      
      if (this.continuousMode && this.onTranscriptCallback) {
        const now = Date.now();
        if (now - this.lastRestartTime > 500 && this.restartAttempts < this.maxRestartAttempts) {
          this.lastRestartTime = now;
          this.restartAttempts++;
          
          setTimeout(() => {
            if (this.continuousMode && this.onTranscriptCallback) {
              try {
                this.recognition.start();
                this.isRecording = true;
              } catch (e) {
                this.restartAttempts = 0;
              }
            }
          }, 100);
        } else if (this.restartAttempts >= this.maxRestartAttempts) {
          this.restartAttempts = 0;
          setTimeout(() => {
            if (this.continuousMode && this.onTranscriptCallback) {
              this.restartAttempts = 0;
              try {
                this.recognition.start();
                this.isRecording = true;
              } catch (e) {}
            }
          }, 1000);
        }
      }
    };
    
    const config = window.NexvaChat?.config;
    if (playIntro && config && config.enableIntroSound && !this.introSoundPlayed) {
      this.introSoundPlayed = true;
      if (!this.introAudio) {
        this.introAudio = new Audio(`${config.apiUrl}/intro.wav`);
        this.introAudio.volume = 0.7;
      }
      
      this.introAudio.onended = () => {
        this.recognition.start();
      };
      
      this.introAudio.onerror = () => {
        this.recognition.start();
      };
      
      this.introAudio.play().catch(() => {
        this.recognition.start();
      });
    } else {
      this.recognition.start();
    }
    
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
      if (this.recognition && (this.isEdge || /android/i.test(navigator.userAgent))) {
        try {
          this.recognition.stop();
        } catch (e) {}
      }
    } else {
      this.clearAssistantTranscript();
      if ((this.isEdge || /android/i.test(navigator.userAgent)) && this.continuousMode && this.onTranscriptCallback) {
        setTimeout(async () => {
          if (!this.assistantSpeaking && this.continuousMode && this.onTranscriptCallback) {
            await this.start(this.onTranscriptCallback, true);
          }
        }, 500);
      }
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
    this.onTranscriptCallback = null;
    this.restartAttempts = 0;
    this.lastRestartTime = 0;
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
    if (this.micStream) {
      this.micStream.getTracks().forEach(track => track.stop());
      this.micStream = null;
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
    this.onTranscriptCallback = null;
    this.introSoundPlayed = false;
    this.restartAttempts = 0;
    this.lastRestartTime = 0;
    const indicator = document.getElementById('nexvaVoiceIndicator');
    if (indicator) {
      indicator.classList.remove('active');
    }
  }
};

