import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import { getLibraryPdfUrl } from '../services/api';

const markdownComponents = {
  h1: ({ children }) => <h1 className="answer-markdown-h1">{children}</h1>,
  h2: ({ children }) => <h2 className="answer-markdown-h2">{children}</h2>,
  h3: ({ children }) => <h3 className="answer-markdown-h3">{children}</h3>,
  p: ({ children }) => <p className="answer-markdown-paragraph">{children}</p>,
  ul: ({ children }) => <ul className="answer-markdown-list">{children}</ul>,
  ol: ({ children }) => <ol className="answer-markdown-list">{children}</ol>,
  li: ({ children }) => <li className="answer-markdown-list-item">{children}</li>,
  blockquote: ({ children }) => (
    <blockquote className="answer-markdown-blockquote">{children}</blockquote>
  ),
  table: ({ children }) => (
    <div className="answer-markdown-table-wrapper">
      <table className="answer-markdown-table">{children}</table>
    </div>
  ),
  hr: () => <hr className="answer-markdown-divider" />,
  a: ({ children, href }) => (
    <a href={href} target="_blank" rel="noopener noreferrer">
      {children}
    </a>
  ),
  pre: ({ children }) => <pre className="answer-markdown-code">{children}</pre>,
  code: ({ children, className }) => (
    <code className={className || 'answer-markdown-inline-code'}>{children}</code>
  )
};

function citationLinkPlugin(sources) {
  const citationPattern = /\[([^\n]+?,\s*p\.\s*(\d+))\]/gi;

  return (tree) => {
    const visit = (node) => {
      if (!Array.isArray(node.children) || node.type === 'link') return;

      node.children = node.children.flatMap((child) => {
        if (child.type !== 'text' || !child.value) {
          visit(child);
          return [child];
        }

        const parts = [];
        let lastIndex = 0;
        let match;
        citationPattern.lastIndex = 0;
        while ((match = citationPattern.exec(child.value)) !== null) {
          if (match.index > lastIndex) {
            parts.push({
              type: 'text',
              value: child.value.slice(lastIndex, match.index)
            });
          }
          const citationName = match[1]
            .replace(/,\s*p\.\s*\d+$/i, '')
            .trim()
            .toLocaleLowerCase();
          const source = sources.find(
            (item) =>
              item.document_id &&
              item.document_name.toLocaleLowerCase() === citationName
          );
          if (source) {
            parts.push({
              type: 'link',
              url: getLibraryPdfUrl(source.document_id, Number(match[2])),
              children: [{ type: 'text', value: match[0] }]
            });
          } else {
            parts.push({ type: 'text', value: match[0] });
          }
          lastIndex = citationPattern.lastIndex;
        }

        if (parts.length === 0) return [child];
        if (lastIndex < child.value.length) {
          parts.push({ type: 'text', value: child.value.slice(lastIndex) });
        }
        return parts;
      });
    };

    visit(tree);
  };
}

function normalizeAnswer(answer) {
  return String(answer || 'No answer was returned.')
    .replace(/\\?<br\s*\/?>/gi, '\n')
    .replace(/&lt;br\s*\/?&gt;/gi, '\n')
    .replace(/&#x20;/gi, ' ');
}

export default function AnswerMarkdown({
  answer,
  sources = [],
  className = ''
}) {
  return (
    <div className={className}>
      <ReactMarkdown
        remarkPlugins={[
          remarkGfm,
          [remarkMath, { singleDollarTextMath: true }],
          [citationLinkPlugin, sources]
        ]}
        rehypePlugins={[[rehypeKatex, { throwOnError: false, strict: 'ignore' }]]}
        components={markdownComponents}
      >
        {normalizeAnswer(answer)}
      </ReactMarkdown>
    </div>
  );
}
