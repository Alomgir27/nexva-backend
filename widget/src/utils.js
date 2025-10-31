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

