import React from 'react';
import { ShieldCheck, Clock, FileCheck, AlertTriangle } from 'lucide-react';

export default function AnswerDisplay({ queryResponse }) {
  if (!queryResponse) return null;

  const { answer, elapsed_time, retrieved_count, is_grounded } = queryResponse;

  return (
    <div className="answer-card">
      <div className="answer-header-bar">
        <div className={`grounded-badge ${is_grounded ? '' : 'un-grounded'}`}>
          {is_grounded ? <ShieldCheck size={14} /> : <AlertTriangle size={14} />}
          {is_grounded ? 'Grounded in Domain Documents' : 'Ungrounded / Notice'}
        </div>

        <div className="meta-stats">
          <Clock size={12} style={{ display: 'inline', marginRight: '3px' }} />
          <span>{elapsed_time}s</span>
          <span style={{ margin: '0 8px' }}>•</span>
          <FileCheck size={12} style={{ display: 'inline', marginRight: '3px' }} />
          <span>{retrieved_count} Chunks Used</span>
        </div>
      </div>

      <div className="answer-body">
        {answer}
      </div>
    </div>
  );
}
