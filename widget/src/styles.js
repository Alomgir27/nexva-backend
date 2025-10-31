export const Styles = {
  inject: function(config) {
    const style = document.createElement('style');
    const primaryColor = config.primaryColor;
    const hoverColor = '#0fdc78';
    const bgBase = '#0a0b0d';
    const bgSecondary = '#121314';
    const bgOverlay = 'rgba(237, 239, 242, 0.04)';
    const textDefault = '#f5f9fe';
    const textSecondary = '#a6aab5';
    const borderColor = 'rgba(255, 255, 255, 0.06)';
    const position = config.position;
    const borderRadius = config.borderRadius;
    const buttonSize = config.buttonSize;
    const buttonColor = config.buttonColor;
    const buttonBorderRadius = config.borderRadius === '0px' ? '0px' : '50%';
    
    style.textContent = `
      .nexva-chat-container { position: fixed; ${position.includes('bottom') ? 'bottom: 20px;' : 'top: 20px;'} ${position.includes('right') ? 'right: 20px;' : 'left: 20px;'} z-index: 999999; font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
      .nexva-chat-button { width: ${buttonSize}; height: ${buttonSize}; background: linear-gradient(135deg, ${buttonColor} 0%, ${hoverColor} 100%); border: none; border-radius: ${buttonBorderRadius}; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 4px 20px rgba(50, 240, 140, 0.4); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
      .nexva-chat-button:hover { transform: translateY(-2px) scale(1.05); box-shadow: 0 8px 30px rgba(50, 240, 140, 0.6); }
      .nexva-chat-button svg { transition: transform 0.3s ease; }
      .nexva-chat-button:hover svg { transform: rotate(-10deg) scale(1.1); }
      .nexva-chat-window { display: none; position: fixed; ${position.includes('bottom') ? 'bottom: 90px;' : 'top: 90px;'} ${position.includes('right') ? 'right: 20px;' : 'left: 20px;'} width: 400px; height: 650px; max-height: calc(100vh - 120px); background: ${bgBase}; border-radius: ${borderRadius}; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4); flex-direction: column; overflow: hidden; border: 1px solid ${borderColor}; }
      .nexva-chat-window.open { display: flex; animation: slideUp 0.3s ease; }
      .nexva-chat-window.fullscreen { width: 100vw; height: 100vh; max-height: 100vh; border-radius: 0; top: 0; bottom: 0; left: 0; right: 0; border: none; }
      .nexva-chat-window.docked { width: 380px; height: 100vh; max-height: 100vh; border-radius: 0; top: 0; bottom: 0; right: 0; left: auto; border-right: none; border-top: none; border-bottom: none; box-shadow: -2px 0 8px rgba(0, 0, 0, 0.15); animation: slideInRight 0.3s ease; }
      @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
      @keyframes slideInRight { from { transform: translateX(100%); } to { transform: translateX(0); } }
      .nexva-chat-header { background: ${bgSecondary}; color: ${textDefault}; padding: 10px 12px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid ${borderColor}; min-height: 44px; }
      .nexva-chat-header-title { display: flex; align-items: center; gap: 8px; overflow: hidden; flex: 1; }
      .nexva-chat-header-title svg { flex-shrink: 0; width: 18px; height: 18px; opacity: 0.8; }
      .nexva-chat-header h3 { margin: 0; font-size: 13px; font-weight: 500; letter-spacing: 0.3px; white-space: nowrap; }
      .nexva-chat-header-actions { display: flex; gap: 0; align-items: center; margin-right: -4px; }
      .nexva-chat-icon-btn { background: transparent; border: none; color: ${textSecondary}; cursor: pointer; padding: 8px; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; transition: all 0.15s ease; opacity: 0.7; }
      .nexva-chat-icon-btn:hover { color: ${textDefault}; opacity: 1; background: rgba(255, 255, 255, 0.03); }
      .nexva-chat-icon-btn svg { width: 15px; height: 15px; }
      .nexva-chat-close:hover { color: #ef4444; background: rgba(239, 68, 68, 0.08); }
      .nexva-chat-tabs { display: flex; background: ${bgBase}; }
      .nexva-chat-tab { flex: 1; padding: 12px 16px; text-align: center; cursor: pointer; border: none; background: ${bgOverlay}; font-size: 13px; font-weight: 500; color: ${textSecondary}; transition: all 0.2s; display: flex; align-items: center; justify-content: center; gap: 8px; }
      .nexva-chat-tab:hover { background: ${bgSecondary}; }
      .nexva-chat-tab.active { background: ${primaryColor}; color: ${bgBase}; }
      .nexva-chat-tab svg { width: 18px; height: 18px; }
      .nexva-chat-messages { flex: 1; overflow-y: auto; padding: 20px; background: ${bgBase}; }
      .nexva-chat-message { margin-bottom: 16px; display: flex; gap: 10px; align-items: flex-start; }
      .nexva-chat-message.user { flex-direction: row-reverse; }
      .nexva-chat-message-content { max-width: 80%; padding: 12px 16px; border-radius: 12px; font-size: 14px; line-height: 1.6; word-wrap: break-word; }
      .nexva-chat-message.assistant .nexva-chat-message-content { background: ${bgSecondary}; color: ${textDefault}; border-radius: 12px 12px 12px 4px; }
      .nexva-chat-message.user .nexva-chat-message-content { background: ${primaryColor}; color: ${bgBase}; border-radius: 12px 12px 4px 12px; font-weight: 500; }
      .nexva-chat-message.system .nexva-chat-message-content { background: ${bgOverlay}; color: ${textSecondary}; text-align: center; max-width: 100%; font-size: 13px; }
      .nexva-chat-message.human { align-items: flex-start; }
      .nexva-human-avatar { width: 32px; height: 32px; min-width: 32px; border-radius: 50%; background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); display: flex; align-items: center; justify-content: center; color: white; }
      .nexva-human-avatar svg { width: 18px; height: 18px; }
      .nexva-human-message-wrapper { flex: 1; max-width: calc(100% - 42px); }
      .nexva-human-name { font-size: 12px; font-weight: 600; color: #7c3aed; margin-bottom: 4px; text-transform: capitalize; }
      .nexva-chat-message.human .nexva-chat-message-content { background: ${bgSecondary}; color: ${textDefault}; border-radius: 12px 12px 12px 4px; border: 1px solid rgba(124, 58, 237, 0.2); max-width: 100%; }
      .nexva-load-more-indicator { text-align: center; padding: 12px; font-size: 12px; color: ${textSecondary}; background: ${bgOverlay}; border-radius: 8px; margin-bottom: 12px; }
      @keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
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
      .nexva-inline-code { background: ${bgOverlay}; padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace; font-size: 0.9em; }
      .nexva-code-block { margin: 12px 0; border-radius: 8px; overflow: hidden; background: ${bgBase}; border: 1px solid ${borderColor}; }
      .nexva-code-header { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: ${bgOverlay}; border-bottom: 1px solid ${borderColor}; }
      .nexva-code-lang { font-size: 12px; color: ${textSecondary}; text-transform: uppercase; font-weight: 500; }
      .nexva-code-copy { padding: 4px 12px; background: ${primaryColor}; color: ${bgBase}; border: none; border-radius: 4px; font-size: 11px; cursor: pointer; transition: all 0.2s; }
      .nexva-code-copy:hover { background: ${hoverColor}; }
      .nexva-code-pre { margin: 0; padding: 12px; overflow-x: auto; }
      .nexva-code-content { font-family: 'JetBrains Mono', monospace; font-size: 13px; line-height: 1.5; color: ${textDefault}; }
      .nexva-chat-input-area { padding: 16px 20px; background: ${bgSecondary}; border-top: 1px solid ${borderColor}; }
      .nexva-mode-switcher { display: flex; gap: 0; background: ${bgOverlay}; border: 1px solid ${borderColor}; overflow: hidden; margin-bottom: 12px; }
      .nexva-mode-btn { 
        flex: 1;
        background: transparent; 
        border: none; 
        padding: 8px 16px; 
        cursor: pointer; 
        transition: all 0.2s ease; 
        opacity: 0.6; 
        display: flex; 
        align-items: center; 
        justify-content: center;
        gap: 6px;
        font-size: 12px;
        color: ${textSecondary};
        font-weight: 500;
        position: relative;
        border-right: 1px solid ${borderColor};
      }
      .nexva-mode-btn:last-child { border-right: none; }
      .nexva-mode-btn svg { width: 16px; height: 16px; }
      .nexva-mode-btn:hover { 
        opacity: 1; 
        background: ${bgSecondary}; 
        color: ${textDefault};
      }
      .nexva-mode-btn.active { 
        opacity: 1; 
        background: ${primaryColor}; 
        color: ${bgBase};
      }
      .nexva-mode-btn::after {
        content: attr(data-tooltip);
        position: absolute;
        top: -36px;
        left: 50%;
        transform: translateX(-50%) scale(0.9);
        background: rgba(0, 0, 0, 0.9);
        color: white;
        padding: 6px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 500;
        white-space: nowrap;
        pointer-events: none;
        opacity: 0;
        transition: all 0.2s ease;
        z-index: 1000;
      }
      .nexva-mode-btn::before {
        content: '';
        position: absolute;
        top: -32px;
        left: 50%;
        transform: translateX(-50%);
        width: 0;
        height: 0;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid rgba(0, 0, 0, 0.9);
        pointer-events: none;
        opacity: 0;
        transition: all 0.2s ease;
        z-index: 1000;
      }
      .nexva-mode-btn:hover::after,
      .nexva-mode-btn:hover::before {
        opacity: 1;
        transform: translateX(-50%) scale(1);
      }
      .nexva-chat-actions { display: flex; gap: 8px; margin-bottom: 12px; }
      .nexva-chat-action-btn { flex: 1; padding: 10px 14px; border: 1px solid ${primaryColor}; background: transparent; color: ${primaryColor}; border-radius: 8px; font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; justify-content: center; gap: 8px; }
      .nexva-chat-action-btn:hover { background: ${primaryColor}; color: ${bgBase}; }
      .nexva-chat-action-btn svg { width: 16px; height: 16px; fill: currentColor; }
      .nexva-chat-input-row { display: flex; gap: 8px; align-items: center; }
      .nexva-chat-voice-prompt { width: 40px; height: 40px; min-width: 40px; border: none; border-radius: 8px; background: ${bgOverlay}; color: ${textSecondary}; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.3s ease; }
      .nexva-chat-voice-prompt:hover { background: ${bgSecondary}; color: ${textDefault}; }
      .nexva-chat-voice-prompt.recording { background: ${primaryColor}; color: white; }
      .nexva-chat-voice-prompt svg { width: 18px; height: 18px; }
      .nexva-chat-input { flex: 1; padding: 12px 16px; border: none; border-radius: 8px; font-size: 14px; outline: none; background: ${bgOverlay}; color: ${textDefault}; transition: all 0.2s; }
      .nexva-chat-input:focus { background: ${bgSecondary}; box-shadow: 0 0 0 1px ${primaryColor}; }
      .nexva-chat-input::placeholder { color: ${textSecondary}; }
      .nexva-chat-btn { width: 44px; height: 44px; min-width: 44px; border: none; border-radius: 50%; background: ${primaryColor}; color: ${bgBase}; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
      .nexva-chat-btn:hover { background: ${hoverColor}; transform: scale(1.05); }
      .nexva-chat-btn:disabled { background: ${bgOverlay}; color: ${textSecondary}; cursor: not-allowed; transform: none; }
      .nexva-chat-btn svg { width: 20px; height: 20px; fill: currentColor; }
      .nexva-chat-btn.recording { background: #ef4444; animation: pulse 1.5s infinite; }
      @keyframes pulse { 0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); } 50% { opacity: 0.8; box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); } }
      .nexva-chat-typing { display: inline-flex; gap: 5px; padding: 12px 16px; background: ${bgSecondary}; border-radius: 12px 12px 12px 4px; }
      .nexva-chat-typing span { width: 8px; height: 8px; background: ${primaryColor}; border-radius: 50%; animation: typing 1.4s infinite; }
      .nexva-chat-typing span:nth-child(2) { animation-delay: 0.2s; }
      .nexva-chat-typing span:nth-child(3) { animation-delay: 0.4s; }
      @keyframes typing { 0%, 60%, 100% { transform: translateY(0); opacity: 0.4; } 30% { transform: translateY(-8px); opacity: 1; } }
      .nexva-chat-voice-indicator { position: fixed; bottom: 110px; ${position.includes('right') ? 'right: 110px;' : 'left: 110px;'} background: ${bgSecondary}; color: ${textDefault}; padding: 14px 24px; border-radius: 12px; font-size: 14px; font-weight: 500; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3); display: none !important; align-items: center; gap: 12px; }
      .nexva-chat-voice-indicator.active { display: none !important; }
      .nexva-chat-voice-wave { display: flex; gap: 4px; }
      .nexva-chat-voice-wave span { width: 3px; height: 18px; background: ${primaryColor}; border-radius: 2px; animation: wave 1s infinite; }
      .nexva-chat-voice-wave span:nth-child(2) { animation-delay: 0.1s; }
      .nexva-chat-voice-wave span:nth-child(3) { animation-delay: 0.2s; }
      .nexva-chat-voice-wave span:nth-child(4) { animation-delay: 0.3s; }
      @keyframes wave { 0%, 100% { height: 18px; } 50% { height: 8px; } }
      @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); } 70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); } 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); } }
      @keyframes subtlePulse { 0% { box-shadow: 0 0 0 0 rgba(79, 70, 229, 0.4); } 50% { box-shadow: 0 0 0 6px rgba(79, 70, 229, 0); } 100% { box-shadow: 0 0 0 0 rgba(79, 70, 229, 0); } }
      @media (max-width: 480px) { .nexva-chat-window { width: calc(100vw - 40px); height: calc(100vh - 120px); } }
      .nexva-chat-messages::-webkit-scrollbar { width: 6px; }
      .nexva-chat-messages::-webkit-scrollbar-track { background: transparent; }
      .nexva-chat-messages::-webkit-scrollbar-thumb { background: ${borderColor}; border-radius: 3px; }
      .nexva-chat-messages::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.15); }
    `;
    document.head.appendChild(style);
  }
};

