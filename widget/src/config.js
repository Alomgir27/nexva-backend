export const Config = {
  defaults: {
    apiUrl: 'http://localhost:8000',
    position: 'bottom-right',
    primaryColor: '#32f08c',
    headerText: 'Nexva',
    welcomeMessage: 'Hi! How can I help you today?',
    placeholder: 'Type your message...',
    enableVoice: true,
    enableHumanSupport: true,
    enableIntroSound: true,
    autoOpen: false,
    theme: 'dark',
    borderRadius: '12px',
    presetQuestions: [],
    bubble: {
      backgroundColor: '#32f08c',
      size: '60px',
      shape: 'circle',
      icon: 'chat',
      iconColor: '#ffffff',
      customIconUrl: '',
      shadow: true,
      animation: 'pulse'
    }
  },
  
  init: function(apiKey, options) {
    options = options || {};
    const primaryColor = options.primaryColor || this.defaults.primaryColor;
    const bubbleDefaults = this.defaults.bubble;
    const bubbleOptions = options.bubble || {};
    
    return {
      apiKey: apiKey,
      apiUrl: options.apiUrl || this.defaults.apiUrl,
      position: options.position || this.defaults.position,
      primaryColor: primaryColor,
      headerText: options.headerText || this.defaults.headerText,
      welcomeMessage: options.welcomeMessage || this.defaults.welcomeMessage,
      placeholder: options.placeholder || this.defaults.placeholder,
      enableVoice: options.enableVoice !== false,
      enableHumanSupport: options.enableHumanSupport !== false,
      enableIntroSound: options.enableIntroSound !== false,
      autoOpen: options.autoOpen || false,
      theme: options.theme || this.defaults.theme,
      borderRadius: options.borderRadius || this.defaults.borderRadius,
      presetQuestions: options.presetQuestions || this.defaults.presetQuestions,
      bubble: {
        backgroundColor: bubbleOptions.backgroundColor || bubbleDefaults.backgroundColor,
        size: bubbleOptions.size || bubbleDefaults.size,
        shape: bubbleOptions.shape || bubbleDefaults.shape,
        icon: bubbleOptions.icon || bubbleDefaults.icon,
        iconColor: bubbleOptions.iconColor || bubbleDefaults.iconColor,
        customIconUrl: bubbleOptions.customIconUrl || bubbleDefaults.customIconUrl,
        shadow: bubbleOptions.shadow !== undefined ? bubbleOptions.shadow : bubbleDefaults.shadow,
        animation: bubbleOptions.animation || bubbleDefaults.animation
      }
    };
  }
};

