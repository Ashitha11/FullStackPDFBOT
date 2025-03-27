import React, { useState } from 'react';

const Chatbot = ({ useVectorDB, useLLM }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMessage = { text: input, sender: 'user' };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');

    if (!useLLM) {
      setMessages((prev) => [...prev, { text: 'Please connect to LLM node', sender: 'bot' }]);
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: input, useVectorDB }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Query failed');
      }
      const data = await response.json();
      const botMessage = { text: data.answer, sender: 'bot' };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error('Query error:', error);
      setMessages((prev) => [...prev, { text: `Error: ${error.message}`, sender: 'bot' }]);
    }
  };

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 10,
        right: 10,
        width: 300,
        height: 400,
        background: '#fff',
        border: '1px solid #ccc',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div style={{ flex: 1, overflowY: 'auto', padding: 10 }}>
        {messages.map((msg, index) => (
          <div
            key={index}
            style={{
              textAlign: msg.sender === 'user' ? 'right' : 'left',
              margin: '5px 0',
            }}
          >
            <span
              style={{
                background: msg.sender === 'user' ? '#007bff' : '#f0f0f0',
                color: msg.sender === 'user' ? '#fff' : '#000',
                padding: '5px 10px',
                borderRadius: 5,
                display: 'inline-block',
              }}
            >
              {msg.text}
            </span>
          </div>
        ))}
      </div>
      <div style={{ padding: 10 }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          style={{ width: '70%', marginRight: 10 }}
        />
        <button onClick={handleSend}>Send</button>
      </div>
    </div>
  );
};

export default Chatbot;