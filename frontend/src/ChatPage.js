import React, { useState, useEffect, useRef, useCallback } from 'react';

function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  
  // Close mobile menu on window resize
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth > 768) {
        setIsMobileMenuOpen(false);
      }
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  const [chatHistory, setChatHistory] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    if (messagesEndRef.current && messages.length > 0) {
      // Find the App element (the actual scrollable container)
      const appContainer = document.querySelector('.App');
      if (appContainer) {
        // Check if user is near bottom (within 100px) before auto-scrolling
        const isNearBottom = appContainer.scrollTop + appContainer.clientHeight >= appContainer.scrollHeight - 100;
        
        // Always scroll for new messages, or if user is already near bottom
        if (isNearBottom || messages.length <= 2) {
          messagesEndRef.current.scrollIntoView({ behavior: "smooth", block: "end" });
        }
      }
    }
  }, [messages.length]);

  useEffect(() => {
    // Auto-scroll when new messages are added
    if (messages.length > 0) {
      scrollToBottom();
    }
  }, [messages.length, scrollToBottom]);

  const generateChatTitle = (message) => {
    // Generate a title from the first message (first few words)
    const words = message.trim().split(' ');
    return words.slice(0, 4).join(' ') + (words.length > 4 ? '...' : '');
  };

  const sendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage = { text: inputValue, sender: 'user', timestamp: Date.now() };
    
    // If this is the first message, create a new chat
    if (messages.length === 0) {
      const newChatId = Date.now();
      const chatTitle = generateChatTitle(inputValue);
      const newChat = {
        id: newChatId,
        title: chatTitle,
        timestamp: new Date().toISOString(),
        messages: [userMessage]
      };
      
      setCurrentChatId(newChatId);
      setChatHistory(prev => [newChat, ...prev]);
      setMessages([userMessage]);
    } else {
      setMessages(prev => [...prev, userMessage]);
      
      // Update current chat in history
      if (currentChatId) {
        setChatHistory(prev => prev.map(chat => 
          chat.id === currentChatId 
            ? { ...chat, messages: [...(chat.messages || []), userMessage] }
            : chat
        ));
      }
    }
    
    setIsLoading(true);

    try {
      setInputValue('');
      
      const response = await fetch('http://localhost:8002/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: inputValue }),
      });

      if (response.ok) {
        const data = await response.json();
        const botMessage = { text: data.response, sender: 'bot', timestamp: Date.now() };
        setMessages(prev => [...prev, botMessage]);
        
        // Update current chat in history
        if (currentChatId) {
          setChatHistory(prev => prev.map(chat => 
            chat.id === currentChatId 
              ? { ...chat, messages: [...(chat.messages || []), botMessage] }
              : chat
          ));
        }
      } else {
        const errorMessage = { text: '❌ Failed to send message. Please try again.', sender: 'bot', timestamp: Date.now() };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      const errorMessage = { text: '❌ Network error. Please check your connection.', sender: 'bot', timestamp: Date.now() };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const TypingIndicator = () => (
    <div className="typing-indicator">
      <div className="typing-dots">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>
  );

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      // Could add a toast notification here if needed
    }).catch(err => {
      console.error('Failed to copy text: ', err);
    });
  };

  const handleLike = (messageIndex) => {
    // Implementation for like functionality
    console.log('Liked message:', messageIndex);
  };

  const handleDislike = (messageIndex) => {
    // Implementation for dislike functionality
    console.log('Disliked message:', messageIndex);
  };


  const newChat = () => {
    setMessages([]);
    setCurrentChatId(null);
    setIsMobileMenuOpen(false);
  };

  const selectChat = (chatId) => {
    const selectedChat = chatHistory.find(chat => chat.id === chatId);
    if (selectedChat) {
      setCurrentChatId(chatId);
      setMessages(selectedChat.messages || []);
      setIsMobileMenuOpen(false);
    }
  };

  const MiniSidebar = () => (
    <div className={`mini-sidebar ${isSidebarCollapsed ? 'show' : ''}`}>
      <button 
        className="mini-sidebar-btn logo-btn" 
        onClick={() => setIsSidebarCollapsed(false)}
        title="Savant Assist - Click to expand"
      >
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
          <rect x="3" y="3" width="18" height="18" rx="4" stroke="#374151" strokeWidth="2" fill="none"/>
          <circle cx="8" cy="8" r="1.5" fill="#374151"/>
          <circle cx="16" cy="8" r="1.5" fill="#374151"/>
          <path d="M8 14c1 2 2.5 3 4 3s3-1 4-3" stroke="#374151" strokeWidth="1.5" strokeLinecap="round"/>
        </svg>
      </button>
      
      <button 
        className="mini-sidebar-btn" 
        onClick={newChat}
        title="New chat"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14,2 14,8 20,8"/>
          <line x1="16" y1="13" x2="8" y2="13"/>
          <line x1="16" y1="17" x2="8" y2="17"/>
          <polyline points="10,9 9,9 8,9"/>
        </svg>
      </button>
      
      <div className="mini-user-avatar" title="John Doe">
        JD
      </div>
    </div>
  );

  const Sidebar = () => (
    <div className={`sidebar ${isSidebarCollapsed ? 'collapsed' : ''} ${isMobileMenuOpen ? 'mobile-open' : ''}`}>
      <div className="sidebar-header">
        <div className="sidebar-title">
          <div className="app-logo">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <rect x="3" y="3" width="18" height="18" rx="4" stroke="#374151" strokeWidth="2" fill="none"/>
              <circle cx="8" cy="8" r="1.5" fill="#374151"/>
              <circle cx="16" cy="8" r="1.5" fill="#374151"/>
              <path d="M8 14c1 2 2.5 3 4 3s3-1 4-3" stroke="#374151" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
          </div>
          <h3>Savant Assist</h3>
        </div>
        <button 
          className="sidebar-close-btn" 
          onClick={() => {
            if (window.innerWidth <= 768) {
              // On mobile, just close the mobile menu
              setIsMobileMenuOpen(false);
            } else {
              // On desktop, collapse the sidebar
              setIsSidebarCollapsed(true);
            }
          }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
            <line x1="9" y1="3" x2="9" y2="21"/>
          </svg>
        </button>
      </div>
      
      <div style={{ padding: '0 12px' }}>
        <button className="new-chat-btn" onClick={newChat}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14,2 14,8 20,8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <polyline points="10,9 9,9 8,9"/>
          </svg>
          New Chat
        </button>
        
        <a href="/admin" className="admin-link" target="_blank" rel="noopener noreferrer">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
          Admin Panel
        </a>
      </div>
      
      <div className="chat-history">
        <h4>Chats</h4>
        {chatHistory.map((chat) => (
        <div key={chat.id} className="chat-history-item" onClick={() => selectChat(chat.id)}>
          <div className="chat-title">{chat.title}</div>
          <div className="chat-date">
            {new Date(chat.timestamp).toLocaleDateString()}
          </div>
        </div>
        ))}
      </div>

      <div className="sidebar-footer">
        <div className="user-profile">
          <div className="user-avatar">
            JD
          </div>
          <div className="user-info">
            <p className="user-name">John Doe</p>
            <p className="user-status">Online</p>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="App">
      {isMobileMenuOpen && <div className="mobile-overlay" onClick={() => setIsMobileMenuOpen(false)} />}
      
      <MiniSidebar />
      <Sidebar />
      <div className={`main-content ${isSidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
        <button 
          className="mobile-menu-toggle"
          onClick={() => {
            setIsMobileMenuOpen(!isMobileMenuOpen);
            if (!isMobileMenuOpen) {
              setIsSidebarCollapsed(false);
            }
          }}
        >
          <svg width="13" height="10" viewBox="0 0 13 10" fill="currentColor">
            <rect x="0" y="0" width="13" height="2" rx="1" fill="currentColor"/>
            <rect x="0" y="4" width="13" height="2" rx="1" fill="currentColor"/>
            <rect x="0" y="8" width="13" height="2" rx="1" fill="currentColor"/>
          </svg>
        </button>
        
        <div className={`chat-container ${messages.length === 0 ? 'welcome-mode' : 'chat-mode'}`}>
          {messages.length === 0 ? (
            <div className="welcome-screen">
              <div className="welcome-content">
                <h2 className="welcome-title">Welcome to Savant Assist</h2>
                <p className="welcome-description">How can I help you today?</p>
              </div>
            </div>
          ) : (
            <>
              <div className="messages-container">
                <div className="messages-wrapper">
                  {messages.map((message, index) => (
                    <div key={`${message.timestamp}-${index}`} className={`message ${message.sender}`}>
                      <span className="text">{message.text}</span>
                    {message.sender === 'bot' && (
                      <div className="message-actions">
                        <button 
                          className="action-btn copy-btn" 
                          onClick={() => copyToClipboard(message.text)}
                          title="Copy message"
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                          </svg>
                        </button>
                        <button 
                          className="action-btn like-btn" 
                          onClick={() => handleLike(index)}
                          title="Like message"
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
                          </svg>
                        </button>
                        <button 
                          className="action-btn dislike-btn" 
                          onClick={() => handleDislike(index)}
                          title="Dislike message"
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path>
                          </svg>
                        </button>
                      </div>
                    )}
                  </div>
                  ))}
                  
                  {isLoading && <TypingIndicator />}
                  <div ref={messagesEndRef} />
                </div>
              </div>
              
              <div className={`input-container ${isSidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
                <div className="input-wrapper">
                  <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Type your message here..."
                    disabled={isLoading}
                  />
                  <button 
                    className="send-button-arrow" 
                    onClick={sendMessage} 
                    disabled={isLoading || !inputValue.trim()}
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                      <polyline points="7,7 17,7 17,17"></polyline>
                    </svg>
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default ChatPage;