"use client";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { useEffect, useRef, useState } from "react";
import { Check, Copy } from "lucide-react";

interface Props {
  content: string;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  function handleCopy() {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }
  return (
    <button
      onClick={handleCopy}
      className="flex items-center gap-1 text-[11px] text-gray-400 hover:text-white transition-colors"
    >
      {copied ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
      {copied ? "Copied!" : "Copy"}
    </button>
  );
}

const VALID_MERMAID_STARTS = ["graph ", "graph\n", "sequenceDiagram", "flowchart ", "flowchart\n", "classDiagram", "stateDiagram", "erDiagram", "gantt", "pie", "gitGraph", "journey", "mindmap", "timeline", "quadrantChart", "xychart"];

function isValidMermaid(chart: string): boolean {
  const trimmed = chart.trim().toLowerCase();
  return VALID_MERMAID_STARTS.some((s) => trimmed.startsWith(s.toLowerCase()));
}

function MermaidBlock({ chart }: { chart: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [fallback, setFallback] = useState(false);

  useEffect(() => {
    if (!isValidMermaid(chart)) { setFallback(true); return; }
    let cancelled = false;
    async function render() {
      try {
        const mermaid = (await import("mermaid")).default;
        mermaid.initialize({ startOnLoad: false, theme: "dark", suppressErrorRendering: true, themeVariables: { background: "#0d1117", primaryColor: "#6366f1", lineColor: "#4b5563", textColor: "#e5e7eb" } });
        const id = `mermaid-${Math.random().toString(36).slice(2)}`;
        const { svg } = await mermaid.render(id, chart.trim());
        if (cancelled) return;
        if (svg.includes("Syntax error") || svg.includes("Parse error")) {
          setFallback(true);
        } else if (ref.current) {
          ref.current.innerHTML = svg;
        }
      } catch {
        if (!cancelled) setFallback(true);
      }
    }
    render();
    return () => { cancelled = true; };
  }, [chart]);

  if (fallback) {
    return (
      <div className="my-3 rounded-lg overflow-hidden border border-gray-700">
        <div className="px-4 py-1.5 bg-gray-800 border-b border-gray-700 flex items-center justify-between">
          <span className="text-[11px] text-gray-400 font-mono uppercase tracking-wider">code</span>
          <CopyButton text={chart} />
        </div>
        <div className="overflow-x-auto">
          <pre className="text-xs text-gray-300 bg-[#0d1117] p-4 leading-relaxed whitespace-pre-wrap">{chart}</pre>
        </div>
      </div>
    );
  }

  return (
    <div className="my-3 rounded-lg overflow-hidden border border-gray-700 bg-[#0d1117]">
      <div className="px-4 py-1.5 bg-gray-800 border-b border-gray-700 flex items-center justify-between">
        <span className="text-[11px] text-gray-400 font-mono uppercase tracking-wider">diagram</span>
        <CopyButton text={chart} />
      </div>
      <div className="p-4 overflow-x-auto">
        <div ref={ref} className="flex justify-center [&>svg]:max-w-full" />
      </div>
    </div>
  );
}

export function MarkdownRenderer({ content }: Props) {
  return (
    <div className="min-w-0 w-full">
      <ReactMarkdown
        components={{
          code({ node, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || "");
            const lang = match?.[1] || "";
            const raw = String(children).replace(/\n$/, "");
            const isBlock = match || raw.includes("\n");

            if (lang === "mermaid") {
              return <MermaidBlock chart={raw} />;
            }

            if (isBlock) {
              return (
                <div className="my-3 rounded-lg overflow-hidden border border-gray-700 min-w-0">
                  <div className="px-4 py-1.5 bg-gray-800 border-b border-gray-700 flex items-center justify-between">
                    <span className="text-[11px] text-gray-400 font-mono uppercase tracking-wider">
                      {lang || "code"}
                    </span>
                    <CopyButton text={raw} />
                  </div>
                  <div className="overflow-x-auto">
                    <SyntaxHighlighter
                      style={vscDarkPlus}
                      language={lang || "text"}
                      PreTag="div"
                      customStyle={{ margin: 0, borderRadius: 0, background: "#0d1117", fontSize: "12.5px", lineHeight: "1.6", padding: "16px", minWidth: 0 }}
                      {...props}
                    >
                      {raw}
                    </SyntaxHighlighter>
                  </div>
                </div>
              );
            }

            return (
              <code className="px-1.5 py-0.5 rounded bg-gray-800 text-gray-200 font-mono text-[12px] break-all" {...props}>
                {children}
              </code>
            );
          },

          p({ children }) {
            return <p className="mb-3 last:mb-0 leading-relaxed break-words">{children}</p>;
          },
          h1({ children }) {
            return <h1 className="text-base font-bold text-white mt-4 mb-2">{children}</h1>;
          },
          h2({ children }) {
            return <h2 className="text-sm font-bold text-white mt-4 mb-2">{children}</h2>;
          },
          h3({ children }) {
            return <h3 className="text-sm font-semibold text-gray-200 mt-3 mb-1">{children}</h3>;
          },
          ul({ children }) {
            return <ul className="list-disc list-inside space-y-1 mb-3 text-gray-300">{children}</ul>;
          },
          ol({ children }) {
            return <ol className="list-decimal list-inside space-y-1 mb-3 text-gray-300">{children}</ol>;
          },
          li({ children }) {
            return <li className="text-sm break-words">{children}</li>;
          },
          strong({ children }) {
            return <strong className="font-semibold text-white">{children}</strong>;
          },
          blockquote({ children }) {
            return (
              <blockquote className="border-l-2 border-brand-500 pl-3 my-2 text-gray-400 italic text-sm">
                {children}
              </blockquote>
            );
          },
          table({ children }) {
            return (
              <div className="overflow-x-auto my-3">
                <table className="text-xs text-gray-300 border-collapse w-full">{children}</table>
              </div>
            );
          },
          th({ children }) {
            return <th className="border border-gray-700 px-3 py-1.5 bg-gray-800 text-left font-medium text-gray-200">{children}</th>;
          },
          td({ children }) {
            return <td className="border border-gray-700 px-3 py-1.5">{children}</td>;
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
