import { NexvaChat } from './src/nexva-chat.js';

window.NexvaChat = NexvaChat;

(function() {
  if (window.__NEXVA_INITIALIZED__) {
    console.log('[Nexva] Widget already initialized, skipping...');
    return;
  }
  window.__NEXVA_INITIALIZED__ = true;
  
  const script = document.currentScript || document.querySelector('script[data-api-key]');
  if (script && script.hasAttribute('data-api-key')) {
    const config = {
      apiKey: script.getAttribute('data-api-key'),
      apiUrl: script.getAttribute('data-api-url'),
      position: script.getAttribute('data-position'),
      primaryColor: script.getAttribute('data-primary-color'),
      headerText: script.getAttribute('data-header-text'),
      welcomeMessage: script.getAttribute('data-welcome-message'),
      placeholder: script.getAttribute('data-placeholder'),
      enableVoice: script.getAttribute('data-enable-voice') === 'true',
      enableHumanSupport: script.getAttribute('data-enable-human-support') === 'true',
      enableIntroSound: script.getAttribute('data-enable-intro-sound') !== 'false',
      enableDock: script.getAttribute('data-enable-dock') !== 'false',
      enableFullscreen: script.getAttribute('data-enable-fullscreen') !== 'false',
      theme: script.getAttribute('data-theme'),
      borderRadius: script.getAttribute('data-border-radius'),
      borderColor: script.getAttribute('data-border-color'),
      borderWidth: script.getAttribute('data-border-width'),
      bubble: {
        backgroundColor: script.getAttribute('data-bubble-bg'),
        size: script.getAttribute('data-bubble-size'),
        shape: script.getAttribute('data-bubble-shape'),
        icon: script.getAttribute('data-bubble-icon'),
        iconColor: script.getAttribute('data-bubble-icon-color'),
        customIconUrl: script.getAttribute('data-bubble-custom-icon'),
        shadow: script.getAttribute('data-bubble-shadow') === 'true',
        animation: script.getAttribute('data-bubble-animation')
      }
    };
    
    const presetQuestions = script.getAttribute('data-preset-questions');
    if (presetQuestions) {
      try {
        config.presetQuestions = JSON.parse(presetQuestions);
      } catch (e) {}
    }
    
    Object.keys(config).forEach(key => {
      if (config[key] === null || config[key] === 'null') delete config[key];
    });
    Object.keys(config.bubble).forEach(key => {
      if (config.bubble[key] === null || config.bubble[key] === 'null') delete config.bubble[key];
    });
    
    NexvaChat.init(config.apiKey, config);
  }
})();
