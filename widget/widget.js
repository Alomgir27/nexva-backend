export { Config } from './src/config.js';
export { Utils } from './src/utils.js';
export { Styles } from './src/styles.js';
export { UI } from './src/ui.js';
export { Messaging } from './src/messaging.js';
export { VoiceChat } from './src/voice.js';
export { WebSocketManager } from './src/websocket.js';
export { NexvaChat } from './src/nexva-chat.js';

if (typeof window !== 'undefined') {
  window.NexvaChat = (await import('./src/nexva-chat.js')).NexvaChat;

  // Auto-initialize from script tag data attributes
  const script = document.currentScript || document.querySelector('script[data-api-key]');
  if (script && script.hasAttribute('data-api-key')) {
    console.log('[Nexva] Auto-initializing from script tag...');

    const apiKey = script.getAttribute('data-api-key');

    // Auto-detect API URL from script src
    let defaultApiUrl = 'https://yueihds3xl383a-5000.proxy.runpod.net';
    if (script.src) {
      try {
        const url = new URL(script.src);
        defaultApiUrl = `${url.protocol}//${url.host}`;
      } catch (e) {
        console.warn('[Nexva] Failed to parse script URL:', e);
      }
    }

    const apiUrl = script.getAttribute('data-api-url') || defaultApiUrl;

    // Parse preset questions if present
    let presetQuestions = [];
    const presetQuestionsAttr = script.getAttribute('data-preset-questions');
    if (presetQuestionsAttr) {
      try {
        presetQuestions = JSON.parse(presetQuestionsAttr);
      } catch (e) {
        console.warn('[Nexva] Failed to parse preset questions:', e);
      }
    }

    // Parse bubble config
    const bubbleConfig = {
      backgroundColor: script.getAttribute('data-bubble-bg') || '#32f08c',
      size: script.getAttribute('data-bubble-size') || '60px',
      shape: script.getAttribute('data-bubble-shape') || 'circle',
      icon: script.getAttribute('data-bubble-icon') || 'chat',
      iconColor: script.getAttribute('data-bubble-icon-color') || '#ffffff',
      customIconUrl: script.getAttribute('data-bubble-custom-icon') || '',
      shadow: script.getAttribute('data-bubble-shadow') !== 'false',
      animation: script.getAttribute('data-bubble-animation') || 'pulse'
    };

    const config = {
      apiUrl: apiUrl,
      position: script.getAttribute('data-position') || 'bottom-right',
      primaryColor: script.getAttribute('data-primary-color') || '#32f08c',
      headerText: script.getAttribute('data-header-text') || 'Nexva Chat',
      welcomeMessage: script.getAttribute('data-welcome-message') || '👋 Hi! How can I help you today?',
      placeholder: script.getAttribute('data-placeholder') || 'Type your message here...',
      enableVoice: script.getAttribute('data-enable-voice') !== 'false',
      enableHumanSupport: script.getAttribute('data-enable-human-support') !== 'false',
      enableIntroSound: script.getAttribute('data-enable-intro-sound') !== 'false',
      enableDock: script.getAttribute('data-enable-dock') !== 'false',
      enableFullscreen: script.getAttribute('data-enable-fullscreen') !== 'false',
      theme: script.getAttribute('data-theme') || 'dark',
      borderRadius: script.getAttribute('data-border-radius') || '12px',
      borderColor: script.getAttribute('data-border-color') || '#E5E7EB',
      borderWidth: script.getAttribute('data-border-width') || '1px',
      presetQuestions: presetQuestions,
      bubble: bubbleConfig,
      buttonSize: bubbleConfig.size,
      buttonColor: bubbleConfig.backgroundColor
    };

    console.log('[Nexva] Initializing with config:', config);

    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => {
        window.NexvaChat.init(apiKey, config);
      });
    } else {
      // DOM is already ready
      window.NexvaChat.init(apiKey, config);
    }
  }
}
