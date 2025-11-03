export const Utils = {
  escapeHtml: function(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  },
  
  generateSessionId: function() {
    return 'widget-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
  },
  
  getOrCreateSessionId: function(apiKey) {
    try {
      const key = `nexva_session_${apiKey}`;
      let sessionId = localStorage.getItem(key);
      
      if (!sessionId) {
        sessionId = this.generateSessionId();
        localStorage.setItem(key, sessionId);
      }
      
      return sessionId;
    } catch (e) {
      return this.generateSessionId();
    }
  },
  
  saveConversationId: function(apiKey, conversationId) {
    try {
      if (!conversationId) {
        return;
      }
      const key = `nexva_conv_${apiKey}`;
      localStorage.setItem(key, conversationId.toString());
    } catch (e) {
      // Failed to save
    }
  },
  
  getConversationId: function(apiKey) {
    try {
      const key = `nexva_conv_${apiKey}`;
      const value = localStorage.getItem(key);
      return value ? parseInt(value, 10) : null;
    } catch (e) {
      return null;
    }
  },
  
  clearConversation: function(apiKey) {
    try {
      const key = `nexva_conv_${apiKey}`;
      localStorage.removeItem(key);
    } catch (e) {
      // Failed to clear
    }
  }
};

