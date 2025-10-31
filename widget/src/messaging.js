import { Utils } from './utils.js';

export const Messaging = {
  isLoadingMore: false,
  hasMoreMessages: true,
  currentConversationId: null,
  apiUrl: null,
  
  init: function(conversationId, apiUrl) {
    this.currentConversationId = conversationId;
    this.apiUrl = apiUrl;
    this.attachScrollListener();
  },
  
  attachScrollListener: function() {
    const container = document.getElementById('nexvaChatMessages');
    if (!container) return;
    
    container.addEventListener('scroll', async () => {
      if (this.isLoadingMore || !this.hasMoreMessages || !this.currentConversationId) return;
      
      if (container.scrollTop < 50) {
        await this.loadMoreMessages();
      }
    });
  },
  
  async loadMoreMessages() {
    if (this.isLoadingMore || !this.hasMoreMessages) return;
    
    const container = document.getElementById('nexvaChatMessages');
    const firstMessage = container.querySelector('.nexva-chat-message[data-message-id]');
    if (!firstMessage) return;
    
    const beforeMessageId = firstMessage.dataset.messageId;
    const oldScrollHeight = container.scrollHeight;
    
    this.isLoadingMore = true;
    this.showLoadingIndicator();
    
    try {
      const response = await fetch(
        `${this.apiUrl}/api/conversations/${this.currentConversationId}/messages?limit=10&before_message_id=${beforeMessageId}`
      );
      
      if (!response.ok) throw new Error('Failed to load messages');
      
      const messages = await response.json();
      
      if (messages.length === 0) {
        this.hasMoreMessages = false;
      } else {
        this.prependMessages(messages);
        const newScrollHeight = container.scrollHeight;
        container.scrollTop = newScrollHeight - oldScrollHeight;
      }
    } catch (error) {
      console.error('Error loading messages:', error);
    } finally {
      this.hideLoadingIndicator();
      this.isLoadingMore = false;
    }
  },
  
  prependMessages: function(messages) {
    const container = document.getElementById('nexvaChatMessages');
    const fragment = document.createDocumentFragment();
    
    messages.forEach(msg => {
      const messageDiv = document.createElement('div');
      messageDiv.className = 'nexva-chat-message ' + msg.role;
      messageDiv.dataset.messageId = msg.id;
      
      if (msg.sender_type === 'support') {
        messageDiv.classList.add('human');
        const agentName = msg.sender_email ? msg.sender_email.split('@')[0] : 'Support';
        messageDiv.innerHTML = `
          <div class="nexva-human-avatar">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
            </svg>
          </div>
          <div class="nexva-human-message-wrapper">
            <div class="nexva-human-name">${agentName}</div>
            <div class="nexva-chat-message-content">${this.formatMarkdown(msg.content)}</div>
          </div>
        `;
      } else if (msg.role === 'assistant') {
        messageDiv.innerHTML = '<div class="nexva-chat-message-content">' + this.formatMarkdown(msg.content) + '</div>';
      } else {
        messageDiv.innerHTML = '<div class="nexva-chat-message-content">' + Utils.escapeHtml(msg.content) + '</div>';
      }
      
      fragment.appendChild(messageDiv);
    });
    
    const firstChild = container.firstChild;
    container.insertBefore(fragment, firstChild);
  },
  
  showLoadingIndicator: function() {
    const container = document.getElementById('nexvaChatMessages');
    const indicator = document.createElement('div');
    indicator.id = 'nexvaLoadMoreIndicator';
    indicator.className = 'nexva-load-more-indicator';
    indicator.textContent = 'Loading...';
    container.insertBefore(indicator, container.firstChild);
  },
  
  hideLoadingIndicator: function() {
    const indicator = document.getElementById('nexvaLoadMoreIndicator');
    if (indicator) indicator.remove();
  },
  
  clearMessages: function() {
    const container = document.getElementById('nexvaChatMessages');
    container.innerHTML = '';
    this.hasMoreMessages = true;
  },
  
  addMessage: function(role, content, messageId = null) {
    const container = document.getElementById('nexvaChatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'nexva-chat-message ' + role;
    if (messageId) {
      messageDiv.dataset.messageId = messageId;
    }
    
    if (role === 'assistant') {
      messageDiv.innerHTML = '<div class="nexva-chat-message-content">' + this.formatMarkdown(content) + '</div>';
    } else {
      messageDiv.innerHTML = '<div class="nexva-chat-message-content">' + Utils.escapeHtml(content) + '</div>';
    }
    
    container.appendChild(messageDiv);
    this.scrollToBottom();
    return { role, content };
  },
  
  addHumanMessage: function(content, senderEmail, messageId = null) {
    const container = document.getElementById('nexvaChatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'nexva-chat-message assistant human';
    if (messageId) {
      messageDiv.dataset.messageId = messageId;
    }
    
    const agentName = senderEmail ? senderEmail.split('@')[0] : 'Support';
    
    messageDiv.innerHTML = `
      <div class="nexva-human-avatar">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
        </svg>
      </div>
      <div class="nexva-human-message-wrapper">
        <div class="nexva-human-name">${agentName}</div>
        <div class="nexva-chat-message-content">${this.formatMarkdown(content)}</div>
      </div>
    `;
    
    container.appendChild(messageDiv);
    this.scrollToBottom();
    return { role: 'assistant', content, sender_type: 'support' };
  },
  
  showTyping: function() {
    const container = document.getElementById('nexvaChatMessages');
    const typing = document.createElement('div');
    typing.className = 'nexva-chat-message assistant';
    typing.id = 'nexvaTyping';
    typing.innerHTML = '<div class="nexva-chat-typing"><span></span><span></span><span></span></div>';
    container.appendChild(typing);
    this.scrollToBottom();
  },
  
  hideTyping: function() {
    const typing = document.getElementById('nexvaTyping');
    if (typing) typing.remove();
  },
  
  appendToLastMessage: function(content) {
    this.hideTyping();
    const container = document.getElementById('nexvaChatMessages');
    let lastMessage = container.querySelector('.nexva-chat-message.assistant:last-child');
    
    if (!lastMessage || lastMessage.dataset.finalized === 'true') {
      lastMessage = document.createElement('div');
      lastMessage.className = 'nexva-chat-message assistant';
      lastMessage.innerHTML = '<div class="nexva-chat-message-content"></div>';
      lastMessage.dataset.rawContent = '';
      container.appendChild(lastMessage);
    }
    
    const contentDiv = lastMessage.querySelector('.nexva-chat-message-content');
    lastMessage.dataset.rawContent = (lastMessage.dataset.rawContent || '') + content;
    contentDiv.innerHTML = this.formatMarkdown(lastMessage.dataset.rawContent);
    this.scrollToBottom();
  },
  
  finalizeMessage: function() {
    const container = document.getElementById('nexvaChatMessages');
    const lastMessage = container.querySelector('.nexva-chat-message.assistant:last-child');
    if (lastMessage) {
      lastMessage.dataset.finalized = 'true';
      const contentDiv = lastMessage.querySelector('.nexva-chat-message-content');
      if (lastMessage.dataset.rawContent) {
        contentDiv.innerHTML = this.formatMarkdown(lastMessage.dataset.rawContent);
      }
    }
  },
  
  scrollToBottom: function() {
    const container = document.getElementById('nexvaChatMessages');
    container.scrollTop = container.scrollHeight;
  },
  
  formatMarkdown: function(text) {
    let html = Utils.escapeHtml(text);
    
    html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
      const language = lang || 'plaintext';
      const codeId = 'code-' + Math.random().toString(36).substr(2, 9);
      return `<div class="nexva-code-block">
        <div class="nexva-code-header">
          <span class="nexva-code-lang">${Utils.escapeHtml(language)}</span>
          <button class="nexva-code-copy" onclick="navigator.clipboard.writeText(document.getElementById('${codeId}').textContent).then(() => { const btn = event.target; btn.textContent = 'Copied!'; setTimeout(() => btn.textContent = 'Copy', 2000); })">Copy</button>
        </div>
        <pre class="nexva-code-pre"><code id="${codeId}" class="nexva-code-content">${code.trim()}</code></pre>
      </div>`;
    });
    
    html = html.replace(/`([^`]+)`/g, '<code class="nexva-inline-code">$1</code>');
    
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="nexva-link">$1</a>');
    
    html = html.replace(/(?<!["=])(https?:\/\/[^\s<>"]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer" class="nexva-link">$1</a>');
    
    html = html.replace(/^### (.+)$/gm, '<h3 class="nexva-h3">$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2 class="nexva-h2">$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1 class="nexva-h1">$1</h1>');
    
    html = html.replace(/^\* (.+)$/gm, '<li class="nexva-li">$1</li>');
    html = html.replace(/^- (.+)$/gm, '<li class="nexva-li">$1</li>');
    html = html.replace(/(<li class="nexva-li">.*<\/li>\n?)+/g, '<ul class="nexva-ul">$&</ul>');
    
    html = html.replace(/^\d+\. (.+)$/gm, '<li class="nexva-li">$1</li>');
    
    html = html.replace(/\n\n/g, '</p><p class="nexva-p">');
    html = '<p class="nexva-p">' + html + '</p>';
    
    html = html.replace(/<p class="nexva-p"><\/p>/g, '');
    html = html.replace(/<p class="nexva-p">(<div|<h[123]|<ul)/g, '$1');
    html = html.replace(/(<\/div>|<\/h[123]>|<\/ul>)<\/p>/g, '$1');
    
    return html;
  }
};

