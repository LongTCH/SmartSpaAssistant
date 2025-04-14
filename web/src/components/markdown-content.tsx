import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { PrismLight as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/cjs/styles/prism";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import { ComponentPropsWithoutRef } from "react";

// Định nghĩa các kiểu dữ liệu
type CodeProps = ComponentPropsWithoutRef<"code"> & {
  node?: any;
  inline?: boolean;
  className?: string;
  children: React.ReactNode;
};

type ComponentTypes = {
  code: React.FC<CodeProps>;
  a: React.FC<ComponentPropsWithoutRef<"a"> & { node?: any }>;
  p: React.FC<ComponentPropsWithoutRef<"p"> & { node?: any }>;
  h1: React.FC<ComponentPropsWithoutRef<"h1"> & { node?: any }>;
  h2: React.FC<ComponentPropsWithoutRef<"h2"> & { node?: any }>;
  h3: React.FC<ComponentPropsWithoutRef<"h3"> & { node?: any }>;
  ul: React.FC<ComponentPropsWithoutRef<"ul"> & { node?: any }>;
  ol: React.FC<ComponentPropsWithoutRef<"ol"> & { node?: any }>;
  li: React.FC<ComponentPropsWithoutRef<"li"> & { node?: any }>;
  blockquote: React.FC<ComponentPropsWithoutRef<"blockquote"> & { node?: any }>;
  hr: React.FC<ComponentPropsWithoutRef<"hr"> & { node?: any }>;
  img: React.FC<ComponentPropsWithoutRef<"img"> & { node?: any }>;
  table: React.FC<ComponentPropsWithoutRef<"table"> & { node?: any }>;
  th: React.FC<ComponentPropsWithoutRef<"th"> & { node?: any }>;
  td: React.FC<ComponentPropsWithoutRef<"td"> & { node?: any }>;
  strong: React.FC<ComponentPropsWithoutRef<"strong"> & { node?: any }>;
  em: React.FC<ComponentPropsWithoutRef<"em"> & { node?: any }>;
};

interface MarkdownContentProps {
  content: string;
  className?: string;
  isDarkTheme?: boolean;
}

export function MarkdownContent({
  content,
  className = "",
  isDarkTheme = false,
}: MarkdownContentProps) {
  // Xác định các lớp CSS dựa trên theme sáng/tối
  const themeClasses = {
    // Text colors
    text: isDarkTheme ? "text-gray-100" : "text-gray-800",
    textMuted: isDarkTheme ? "text-gray-300" : "text-gray-600",

    // Background colors
    bg: isDarkTheme ? "bg-gray-800" : "bg-white",
    bgSecondary: isDarkTheme ? "bg-gray-700" : "bg-gray-100",
    bgCode: isDarkTheme ? "bg-gray-900" : "bg-gray-100",

    // Border colors
    border: isDarkTheme ? "border-gray-600" : "border-gray-300",

    // Link colors
    link: isDarkTheme
      ? "text-blue-300 hover:text-blue-200"
      : "text-blue-600 hover:text-blue-800",

    // Code block colors
    codeText: isDarkTheme ? "text-gray-100" : "text-gray-800",
    codeInline: isDarkTheme
      ? "bg-gray-700 text-gray-100"
      : "bg-gray-100 text-gray-800",
  };

  // Xác định các components cho ReactMarkdown
  const components: Partial<ComponentTypes> = {
    code({ node, inline, className, children, ...props }) {
      const match = /language-(\w+)/.exec(className || "");

      return !inline && match ? (
        <div className="overflow-hidden rounded-md my-4">
          <SyntaxHighlighter
            // @ts-ignore - Bỏ qua lỗi TypeScript cho style
            style={vscDarkPlus}
            language={match[1]}
            PreTag="div"
            {...props}
          >
            {String(children).replace(/\n$/, "")}
          </SyntaxHighlighter>
        </div>
      ) : (
        <code
          className={`${className} px-1 py-0.5 rounded ${themeClasses.codeInline}`}
          {...props}
        >
          {children}
        </code>
      );
    },
    a: ({ node, ...props }) => (
      <a
        {...props}
        target="_blank"
        rel="noopener noreferrer"
        className={`${themeClasses.link} hover:underline`}
      />
    ),
    p: ({ node, ...props }) => <p className="mb-4 last:mb-0" {...props} />,
    h1: ({ node, ...props }) => (
      <h1 className="text-xl font-bold mb-2" {...props} />
    ),
    h2: ({ node, ...props }) => (
      <h2 className="text-lg font-bold mb-2" {...props} />
    ),
    h3: ({ node, ...props }) => (
      <h3 className="text-base font-bold mb-2" {...props} />
    ),
    ul: ({ node, ...props }) => (
      <ul className="list-disc ml-5 mb-4" {...props} />
    ),
    ol: ({ node, ...props }) => (
      <ol className="list-decimal ml-5 mb-4" {...props} />
    ),
    li: ({ node, ...props }) => <li className="mb-1" {...props} />,
    blockquote: ({ node, ...props }) => (
      <blockquote
        className={`border-l-4 ${themeClasses.border} pl-4 italic ${themeClasses.textMuted} my-4`}
        {...props}
      />
    ),
    hr: ({ node, ...props }) => (
      <hr className={`border-t ${themeClasses.border} my-4`} {...props} />
    ),
    img: ({ node, alt, ...props }) => (
      <img
        alt={alt || "Image"}
        className="max-w-full h-auto rounded my-4"
        {...props}
      />
    ),
    table: ({ node, ...props }) => (
      <div className="overflow-x-auto my-4">
        <table
          className={`border-collapse border ${themeClasses.border}`}
          {...props}
        />
      </div>
    ),
    th: ({ node, ...props }) => (
      <th
        className={`border ${themeClasses.border} px-4 py-2 ${themeClasses.bgSecondary}`}
        {...props}
      />
    ),
    td: ({ node, ...props }) => (
      <td className={`border ${themeClasses.border} px-4 py-2`} {...props} />
    ),
    strong: ({ node, ...props }) => <strong className="font-bold" {...props} />,
    em: ({ node, ...props }) => <em className="italic" {...props} />,
  };

  // Loại bỏ prop className khỏi ReactMarkdown và đặt nó vào div wrapper
  return (
    <div className={`${className} ${themeClasses.text}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeRaw, rehypeKatex]}
        // @ts-ignore - Bỏ qua lỗi TypeScript cho components
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
