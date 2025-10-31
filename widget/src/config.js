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
    autoOpen: false,
    theme: 'light',
    borderRadius: '12px',
    buttonIcon: 'chat',
    buttonSize: '60px',
    buttonColor: null
  },
  
  init: function(apiKey, options) {
    options = options || {};
    const primaryColor = options.primaryColor || this.defaults.primaryColor;
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
      autoOpen: options.autoOpen || false,
      theme: options.theme || this.defaults.theme,
      borderRadius: options.borderRadius || this.defaults.borderRadius,
      buttonIcon: options.buttonIcon || this.defaults.buttonIcon,
      buttonSize: options.buttonSize || this.defaults.buttonSize,
      buttonColor: options.buttonColor || primaryColor
    };
  }
};

