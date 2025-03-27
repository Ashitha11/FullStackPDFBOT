import React from 'react';
import { Handle } from '@xyflow/react';

const LLMNode = () => (
  <div style={{ padding: 10, background: '#fff', border: '1px solid #ddd' }}>
    <Handle type="target" position="left" />
    <Handle type="source" position="right" />
    <h4>OpenAI LLM</h4>
  </div>
);

export default LLMNode;