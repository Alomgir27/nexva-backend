export const Styles = {
  inject: function (config) {
    const style = document.createElement('style');
    const primaryColor = config.primaryColor;
    const hoverColor = '#0fdc78';
    const bgBase = '#0a0b0d';
    const bgSecondary = '#141517';
    const bgTertiary = '#1a1b1e';
    const bgOverlay = 'rgba(255, 255, 255, 0.03)';
    const textDefault = '#f5f9fe';
    const textSecondary = '#9ca3af';
    const borderColor = 'rgba(255, 255, 255, 0.08)';
    const position = config.position;
    const borderRadius = config.borderRadius;
    const buttonSize = config.buttonSize;
    const buttonColor = config.buttonColor;
    const buttonBorderRadius = config.borderRadius === '0px' ? '0px' : '50%';

    style.textContent = `
      * { box-sizing: border-box; }
      
      .nexva-chat-container { 
        position: fixed; 
        ${position.includes('bottom') ? 'bottom: 20px;' : 'top: 20px;'} 
        ${position.includes('right') ? 'right: 20px;' : 'left: 20px;'} 
        z-index: 999999; 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", sans-serif;
      }
      
      .nexva-chat-button { 
        width: ${buttonSize}; 
        height: ${buttonSize}; 
        background: linear-gradient(135deg, ${buttonColor} 0%, ${hoverColor} 100%); 
        border: none; 
        border-radius: ${buttonBorderRadius}; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        cursor: pointer; 
        box-shadow: 0 8px 24px rgba(15, 220, 120, 0.3); 
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
      }
      .nexva-chat-button:hover { 
        transform: translateY(-3px) scale(1.05); 
        box-shadow: 0 12px 32px rgba(15, 220, 120, 0.5); 
      }
      .nexva-chat-button:active {
        transform: translateY(-1px) scale(1.02);
      }
      .nexva-chat-button svg { 
        transition: transform 0.3s ease; 
      }
      .nexva-chat-button:hover svg { 
        transform: scale(1.1); 
      }
      
      .nexva-chat-window { 
        display: none; 
        position: fixed; 
        ${position.includes('bottom') ? 'bottom: 90px;' : 'top: 90px;'} 
        ${position.includes('right') ? 'right: 20px;' : 'left: 20px;'} 
        width: 400px; 
        height: 600px; 
        max-height: calc(100vh - 120px); 
        background: ${bgBase}; 
        border-radius: 16px; 
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6), 0 0 1px ${borderColor}; 
        flex-direction: column; 
        overflow: hidden; 
        backdrop-filter: blur(10px);
      }
      .nexva-chat-window.open { 
        display: flex; 
        animation: slideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1); 
      }
      .nexva-chat-window.fullscreen { 
        width: 100vw; 
        height: 100vh; 
        max-height: 100vh; 
        border-radius: 0; 
        top: 0; 
        bottom: 0; 
        left: 0; 
        right: 0; 
        box-shadow: none;
      }
      .nexva-chat-window.docked { 
        width: 400px; 
        height: 100vh; 
        max-height: 100vh; 
        border-radius: 0; 
        top: 0; 
        bottom: 0; 
        right: 0; 
        left: auto; 
        box-shadow: -4px 0 20px rgba(0, 0, 0, 0.3); 
        animation: slideInRight 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
      }
      
      @keyframes slideUp { 
        from { opacity: 0; transform: translateY(30px) scale(0.95); } 
        to { opacity: 1; transform: translateY(0) scale(1); } 
      }
      @keyframes slideInRight { 
        from { transform: translateX(100%); } 
        to { transform: translateX(0); } 
      }
      
      .nexva-chat-header { 
        background: ${bgSecondary}; 
        color: ${textDefault}; 
        padding: 16px; 
        display: flex; 
        flex-direction: column; 
        gap: 12px; 
        border-bottom: 1px solid ${borderColor}; 
      }
      
      .nexva-chat-header-top { 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        gap: 12px; 
      }
      
      .nexva-chat-header-title { 
        display: flex; 
        align-items: center; 
        gap: 10px; 
        overflow: hidden; 
        flex: 1; 
      }
      .nexva-chat-header-title svg { 
        flex-shrink: 0; 
        width: 20px; 
        height: 20px; 
        color: ${primaryColor}; 
      }
      .nexva-chat-header h3 { 
        margin: 0; 
        font-size: 15px; 
        font-weight: 600; 
        letter-spacing: -0.01em; 
        white-space: nowrap; 
        color: ${textDefault};
      }
      
      .nexva-chat-header-actions { 
        display: flex; 
        gap: 4px; 
        align-items: center; 
        flex-shrink: 0; 
      }
      
      .nexva-chat-icon-btn { 
        background: ${bgOverlay}; 
        border: none; 
        color: ${textSecondary}; 
        cursor: pointer; 
        padding: 0; 
        width: 36px; 
        height: 36px; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        transition: all 0.2s ease; 
        border-radius: 8px;
      }
      .nexva-chat-icon-btn:hover { 
        color: ${textDefault}; 
        background: rgba(255, 255, 255, 0.08); 
        transform: scale(1.05);
      }
      .nexva-chat-icon-btn:active {
        transform: scale(0.95);
      }
      .nexva-chat-icon-btn svg { 
        width: 18px; 
        height: 18px; 
      }
      .nexva-chat-close:hover { 
        color: #ef4444; 
        background: rgba(239, 68, 68, 0.1); 
      }
      
      .nexva-mode-switcher { 
        display: flex; 
        gap: 8px; 
        padding: 4px; 
        background: ${bgBase}; 
        border-radius: 10px; 
        width: 100%;
        border: 1px solid ${borderColor};
      }
      
      .nexva-mode-btn { 
        flex: 1; 
        background: transparent; 
        border: none; 
        padding: 10px 16px; 
        cursor: pointer; 
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        gap: 8px; 
        color: ${textSecondary}; 
        border-radius: 8px; 
        font-size: 14px;
        font-weight: 500;
        position: relative;
      }
      .nexva-mode-btn svg { 
        width: 18px; 
        height: 18px; 
      }
      .nexva-mode-btn:hover { 
        background: ${bgOverlay}; 
        color: ${textDefault}; 
      }
      .nexva-mode-btn.active { 
        background: linear-gradient(135deg, ${primaryColor} 0%, ${hoverColor} 100%); 
        color: ${bgBase}; 
        box-shadow: 0 4px 12px rgba(15, 220, 120, 0.3);
        font-weight: 600;
      }
      .nexva-mode-btn.active:hover {
        transform: scale(1.02);
      }
      
      .nexva-chat-messages { 
        flex: 1; 
        overflow-y: auto; 
        padding: 20px; 
        background: ${bgBase}; 
      }
      
      .nexva-chat-message { 
        margin-bottom: 16px; 
        display: flex; 
        gap: 10px; 
        align-items: flex-start; 
        animation: messageSlide 0.3s ease;
      }
      @keyframes messageSlide {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
      }
      .nexva-chat-message.user { 
        flex-direction: row-reverse; 
      }
      
      .nexva-chat-message-content { 
        max-width: 75%; 
        padding: 12px 16px; 
        border-radius: 12px; 
        font-size: 14px; 
        line-height: 1.5; 
        word-wrap: break-word; 
      }
      .nexva-chat-message.assistant .nexva-chat-message-content { 
        background: ${bgTertiary}; 
        color: ${textDefault}; 
        border-radius: 12px 12px 12px 2px;
      }
      .nexva-chat-message.user .nexva-chat-message-content { 
        background: linear-gradient(135deg, ${primaryColor} 0%, ${hoverColor} 100%); 
        color: ${bgBase}; 
        border-radius: 12px 12px 2px 12px; 
        font-weight: 500; 
        box-shadow: 0 4px 12px rgba(15, 220, 120, 0.2);
      }
      .nexva-chat-message.system .nexva-chat-message-content { 
        background: ${bgOverlay}; 
        color: ${textSecondary}; 
        text-align: center; 
        max-width: 100%; 
        font-size: 13px;
        border-radius: 8px;
        padding: 8px 12px;
      }
      
      .nexva-chat-message.human { 
        align-items: flex-start; 
      }
      .nexva-human-avatar { 
        width: 32px; 
        height: 32px; 
        min-width: 32px; 
        border-radius: 50%; 
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        color: white; 
      }
      .nexva-human-avatar svg { 
        width: 18px; 
        height: 18px; 
      }
      .nexva-human-message-wrapper { 
        flex: 1; 
        max-width: calc(100% - 42px); 
      }
      .nexva-human-name { 
        font-size: 11px; 
        font-weight: 600; 
        color: #8b5cf6; 
        margin-bottom: 4px; 
        letter-spacing: 0.3px; 
      }
      .nexva-chat-message.human .nexva-chat-message-content { 
        background: ${bgTertiary}; 
        color: ${textDefault}; 
        border-radius: 12px 12px 12px 2px; 
        border: 1px solid rgba(139, 92, 246, 0.2); 
        max-width: 100%; 
      }
      
      .nexva-load-more-indicator { 
        text-align: center; 
        padding: 10px; 
        font-size: 12px; 
        color: ${textSecondary}; 
        background: ${bgOverlay}; 
        border-radius: 8px; 
        margin-bottom: 12px; 
      }
      
      .nexva-p { margin: 8px 0; line-height: 1.6; }
      .nexva-p:first-child { margin-top: 0; }
      .nexva-p:last-child { margin-bottom: 0; }
      .nexva-h1, .nexva-h2, .nexva-h3 { margin: 16px 0 8px; font-weight: 600; line-height: 1.3; }
      .nexva-h1 { font-size: 1.5em; }
      .nexva-h2 { font-size: 1.3em; }
      .nexva-h3 { font-size: 1.1em; }
      .nexva-ul { margin: 8px 0; padding-left: 24px; }
      .nexva-li { margin: 4px 0; }
      .nexva-link { color: ${primaryColor}; text-decoration: underline; }
      .nexva-link:hover { color: ${hoverColor}; }
      .nexva-inline-code { background: ${bgOverlay}; padding: 2px 6px; border-radius: 4px; font-family: 'SF Mono', 'Monaco', monospace; font-size: 0.9em; }
      .nexva-code-block { margin: 12px 0; border-radius: 8px; overflow: hidden; background: ${bgBase}; border: 1px solid ${borderColor}; }
      .nexva-code-header { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: ${bgOverlay}; border-bottom: 1px solid ${borderColor}; }
      .nexva-code-lang { font-size: 12px; color: ${textSecondary}; text-transform: uppercase; font-weight: 500; }
      .nexva-code-copy { padding: 4px 12px; background: ${primaryColor}; color: ${bgBase}; border: none; border-radius: 4px; font-size: 11px; cursor: pointer; transition: all 0.2s; }
      .nexva-code-copy:hover { background: ${hoverColor}; }
      .nexva-code-pre { margin: 0; padding: 12px; overflow-x: auto; }
      .nexva-code-content { font-family: 'SF Mono', 'Monaco', monospace; font-size: 13px; line-height: 1.5; color: ${textDefault}; }
      
      .nexva-chat-input-area { 
        padding: 16px; 
        background: ${bgSecondary}; 
        border-top: 1px solid ${borderColor}; 
      }
      
      .nexva-chat-actions { 
        display: flex; 
        gap: 8px; 
        margin-bottom: 12px; 
      }
      .nexva-chat-action-btn { 
        flex: 1; 
        padding: 10px 14px; 
        border: 1px solid ${primaryColor}; 
        background: transparent; 
        color: ${primaryColor}; 
        border-radius: 8px; 
        font-size: 13px; 
        font-weight: 500; 
        cursor: pointer; 
        transition: all 0.2s; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        gap: 8px; 
      }
      .nexva-chat-action-btn:hover { 
        background: ${primaryColor}; 
        color: ${bgBase}; 
      }
      .nexva-chat-action-btn svg { 
        width: 16px; 
        height: 16px; 
        fill: currentColor; 
      }
      
      .nexva-chat-input-row { 
        display: flex; 
        gap: 10px; 
        align-items: center; 
      }
      
      .nexva-chat-voice-btn { 
        width: 42px; 
        height: 42px; 
        min-width: 42px; 
        border: none; 
        border-radius: 10px; 
        background: ${bgTertiary}; 
        color: ${textSecondary}; 
        cursor: pointer; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
      }
      .nexva-chat-voice-btn:hover { 
        background: linear-gradient(135deg, ${primaryColor} 0%, ${hoverColor} 100%); 
        color: ${bgBase}; 
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(15, 220, 120, 0.3);
      }
      .nexva-chat-voice-btn:active {
        transform: translateY(0);
      }
      .nexva-chat-voice-btn[data-voice-active="true"] { 
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); 
        color: white; 
        animation: voicePulse 2s cubic-bezier(0.4, 0, 0.2, 1) infinite;
        box-shadow: 0 4px 16px rgba(239, 68, 68, 0.4);
      }
      .nexva-chat-voice-btn[data-voice-active="true"]:hover {
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
        box-shadow: 0 6px 20px rgba(239, 68, 68, 0.5);
      }
      @keyframes voicePulse { 
        0%, 100% { box-shadow: 0 4px 16px rgba(239, 68, 68, 0.4), 0 0 0 0 rgba(239, 68, 68, 0.7); } 
        50% { box-shadow: 0 4px 16px rgba(239, 68, 68, 0.4), 0 0 0 6px rgba(239, 68, 68, 0); } 
      }
      .nexva-chat-voice-btn svg { 
        width: 20px; 
        height: 20px; 
      }
      
      .nexva-chat-input { 
        flex: 1; 
        padding: 11px 14px; 
        border: 1px solid ${borderColor}; 
        border-radius: 10px; 
        font-size: 14px; 
        outline: none; 
        background: ${bgBase}; 
        color: ${textDefault}; 
        transition: all 0.2s ease; 
        font-family: inherit;
      }
      .nexva-chat-input:focus { 
        background: ${bgBase}; 
        border-color: ${primaryColor}; 
        box-shadow: 0 0 0 3px rgba(15, 220, 120, 0.1); 
      }
      .nexva-chat-input:disabled { 
        opacity: 0.5; 
        cursor: not-allowed; 
      }
      .nexva-chat-input::placeholder { 
        color: ${textSecondary}; 
      }
      
      .nexva-chat-btn { 
        width: 42px; 
        height: 42px; 
        min-width: 42px; 
        border: none; 
        border-radius: 10px; 
        background: linear-gradient(135deg, ${primaryColor} 0%, ${hoverColor} 100%); 
        color: ${bgBase}; 
        cursor: pointer; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
        box-shadow: 0 4px 12px rgba(15, 220, 120, 0.3);
      }
      .nexva-chat-btn:hover { 
        background: linear-gradient(135deg, ${hoverColor} 0%, ${primaryColor} 100%); 
        transform: translateY(-2px); 
        box-shadow: 0 6px 16px rgba(15, 220, 120, 0.4); 
      }
      .nexva-chat-btn:active {
        transform: translateY(0);
      }
      .nexva-chat-btn:disabled { 
        background: ${bgOverlay}; 
        color: ${textSecondary}; 
        cursor: not-allowed; 
        transform: none; 
        box-shadow: none;
      }
      .nexva-chat-btn svg { 
        width: 20px; 
        height: 20px; 
        fill: currentColor; 
      }
      
      .nexva-chat-typing { 
        display: inline-flex; 
        gap: 5px; 
        padding: 12px 16px; 
        background: ${bgTertiary}; 
        border-radius: 12px 12px 12px 2px;
        border: 1px solid ${borderColor};
      }
      .nexva-chat-typing span { 
        width: 8px; 
        height: 8px; 
        background: ${primaryColor}; 
        border-radius: 50%; 
        animation: typing 1.4s infinite; 
      }
      .nexva-chat-typing span:nth-child(2) { 
        animation-delay: 0.2s; 
      }
      .nexva-chat-typing span:nth-child(3) { 
        animation-delay: 0.4s; 
      }
      @keyframes typing { 
        0%, 60%, 100% { transform: translateY(0); opacity: 0.4; } 
        30% { transform: translateY(-8px); opacity: 1; } 
      }
      
      .nexva-chat-voice-indicator { 
        position: fixed; 
        bottom: 110px; 
        ${position.includes('right') ? 'right: 110px;' : 'left: 110px;'} 
        background: ${bgSecondary}; 
        color: ${textDefault}; 
        padding: 14px 24px; 
        border-radius: 12px; 
        font-size: 14px; 
        font-weight: 500; 
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3); 
        display: none; 
        align-items: center; 
        gap: 12px; 
        border: 1px solid ${borderColor};
      }
      .nexva-chat-voice-indicator.active { 
        display: flex; 
      }
      .nexva-chat-voice-indicator.speaking .nexva-chat-voice-wave {
        display: none;
      }
      
      .nexva-voice-interrupt-btn {
        display: none;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        background: rgba(239, 68, 68, 0.9); /* Red background */
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 24px;
        color: white;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        backdrop-filter: blur(8px);
        margin-left: 12px;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
        animation: slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        z-index: 10;
      }
      
      .nexva-voice-interrupt-btn:hover {
        background: #dc2626;
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 6px 16px rgba(239, 68, 68, 0.4);
      }
      
      .nexva-voice-interrupt-btn:active {
        transform: translateY(0) scale(0.98);
      }
      
      @keyframes slideIn {
        from { opacity: 0; transform: translateX(10px); }
        to { opacity: 1; transform: translateX(0); }
      }
      
      .nexva-chat-voice-wave { 
        display: flex; 
        gap: 4px; 
      }
      .nexva-chat-voice-wave span { 
        width: 3px; 
        height: 18px; 
        background: ${primaryColor}; 
        border-radius: 2px; 
        animation: wave 1s infinite; 
      }
      .nexva-chat-voice-wave span:nth-child(2) { 
        animation-delay: 0.1s; 
      }
      .nexva-chat-voice-wave span:nth-child(3) { 
        animation-delay: 0.2s; 
      }
      .nexva-chat-voice-wave span:nth-child(4) { 
        animation-delay: 0.3s; 
      }
      @keyframes wave { 
        0%, 100% { height: 18px; } 
        50% { height: 8px; } 
      }
      
      @media (max-width: 480px) { 
        .nexva-chat-window { 
          width: calc(100vw - 24px); 
          height: calc(100vh - 110px); 
          right: 12px !important;
          left: 12px !important;
          bottom: 80px !important;
        } 
        .nexva-chat-container { 
          bottom: 12px !important; 
          right: 12px !important; 
          left: auto !important;
        }
        .nexva-chat-window.docked {
          width: 100vw;
          right: 0 !important;
          left: 0 !important;
        }
      }
      
      .nexva-chat-messages::-webkit-scrollbar { 
        width: 6px; 
      }
      .nexva-chat-messages::-webkit-scrollbar-track { 
        background: transparent; 
      }
      .nexva-chat-messages::-webkit-scrollbar-thumb { 
        background: ${borderColor}; 
        border-radius: 3px; 
      }
      .nexva-chat-messages::-webkit-scrollbar-thumb:hover { 
        background: rgba(255, 255, 255, 0.15); 
      }
    `;
    document.head.appendChild(style);
  }
};
