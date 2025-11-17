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
}
