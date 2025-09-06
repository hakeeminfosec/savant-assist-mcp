import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage = { text: inputValue, sender: 'user', timestamp: Date.now() };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/chat', {
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
      } else {
        const errorMessage = { text: '❌ Failed to send message. Please try again.', sender: 'bot', timestamp: Date.now() };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      const errorMessage = { text: '🔌 Could not connect to server. Check if the backend is running.', sender: 'bot', timestamp: Date.now() };
      setMessages(prev => [...prev, errorMessage]);
    }

    setInputValue('');
    setIsLoading(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const TypingIndicator = () => (
    <div className="message bot">
      <div className="typing-indicator">
        <span>Typing</span>
        <div className="typing-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
  );

  return (
    <div className="App">
      <div className="chat-container">
        <div className="messages-container">
          {messages.length === 0 && (
            <div className="welcome-message">
              <div className="welcome-content">
                <h2 className="welcome-title">Welcome to Professional Assistant</h2>
                <p className="welcome-description">
                  Your intelligent conversation partner for productivity, problem-solving, and expert assistance. 
                  Start by typing your message below.
                </p>
                <div className="welcome-features">
                  <div className="feature">
                    <span className="feature-icon">💬</span>
                    <span className="feature-text">Natural conversation</span>
                  </div>
                  <div className="feature">
                    <span className="feature-icon">🎯</span>
                    <span className="feature-text">Instant responses</span>
                  </div>
                  <div className="feature">
                    <span className="feature-icon">🔒</span>
                    <span className="feature-text">Secure & private</span>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {messages.map((message, index) => (
            <div key={`${message.timestamp}-${index}`} className={`message ${message.sender}`}>
              <span className="text">{message.text}</span>
            </div>
          ))}
          
          {isLoading && <TypingIndicator />}
          <div ref={messagesEndRef} />
        </div>
        
        <div className="input-container">
          <div className="input-wrapper">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message here..."
              disabled={isLoading}
              maxLength={1000}
            />
          </div>
          <button 
            className="send-button" 
            onClick={sendMessage} 
            disabled={isLoading || !inputValue.trim()}
          >
            {isLoading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;