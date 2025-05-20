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
  inline?: boolean;
  className?: string;
  children: React.ReactNode;
};

type ComponentTypes = {
  code: React.FC<CodeProps>;
  a: React.FC<ComponentPropsWithoutRef<"a">>;
  p: React.FC<ComponentPropsWithoutRef<"p">>;
  h1: React.FC<ComponentPropsWithoutRef<"h1">>;
  h2: React.FC<ComponentPropsWithoutRef<"h2">>;
  h3: React.FC<ComponentPropsWithoutRef<"h3">>;
  ul: React.FC<ComponentPropsWithoutRef<"ul">>;
  ol: React.FC<ComponentPropsWithoutRef<"ol">>;
  li: React.FC<ComponentPropsWithoutRef<"li">>;
  blockquote: React.FC<ComponentPropsWithoutRef<"blockquote">>;
  hr: React.FC<ComponentPropsWithoutRef<"hr">>;
  img: React.FC<ComponentPropsWithoutRef<"img">>;
  table: React.FC<ComponentPropsWithoutRef<"table">>;
  th: React.FC<ComponentPropsWithoutRef<"th">>;
  td: React.FC<ComponentPropsWithoutRef<"td">>;
  strong: React.FC<ComponentPropsWithoutRef<"strong">>;
  em: React.FC<ComponentPropsWithoutRef<"em">>;
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
    code({ inline, className, children, ...props }) {
      const match = /language-(\w+)/.exec(className || "");

      return !inline && match ? (
        <div className="overflow-hidden rounded-md my-4">
          <SyntaxHighlighter
            // @ts-expect-error - rehype-raw is not yet updated for React 19
            style={vscDarkPlus}
            language={match[1]}
            PreTag="div"
            {...props}
          >
            {String(children).replace(/\n+$/, "")}
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
    a: ({ ...props }) => (
      <a
        {...props}
        target="_blank"
        rel="noopener noreferrer"
        className={`${themeClasses.link} hover:underline`}
      />
    ),
    p: ({ ...props }) => <p className="mb-4 last:mb-0" {...props} />,
    h1: ({ ...props }) => <h1 className="text-xl font-bold mb-2" {...props} />,
    h2: ({ ...props }) => <h2 className="text-lg font-bold mb-2" {...props} />,
    h3: ({ ...props }) => (
      <h3 className="text-base font-bold mb-2" {...props} />
    ),
    ul: ({ ...props }) => <ul className="list-disc ml-5 mb-4" {...props} />,
    ol: ({ ...props }) => <ol className="list-decimal ml-5 mb-4" {...props} />,
    li: ({ ...props }) => <li className="mb-1" {...props} />,
    blockquote: ({ ...props }) => (
      <blockquote
        className={`border-l-4 ${themeClasses.border} pl-4 italic ${themeClasses.textMuted} my-4`}
        {...props}
      />
    ),
    hr: ({ ...props }) => (
      <hr className={`border-t ${themeClasses.border} my-4`} {...props} />
    ),
    img: ({ alt, ...props }) => (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        alt={alt || "Image"}
        className="max-w-full h-auto rounded my-4"
        {...props}
      />
    ),
    table: ({ ...props }) => (
      <div className="overflow-x-auto my-4">
        <table
          className={`border-collapse border ${themeClasses.border}`}
          {...props}
        />
      </div>
    ),
    th: ({ ...props }) => (
      <th
        className={`border ${themeClasses.border} px-4 py-2 ${themeClasses.bgSecondary}`}
        {...props}
      />
    ),
    td: ({ ...props }) => (
      <td className={`border ${themeClasses.border} px-4 py-2`} {...props} />
    ),
    strong: ({ ...props }) => <strong className="font-bold" {...props} />,
    em: ({ ...props }) => <em className="italic" {...props} />,
  };

  // Loại bỏ prop className khỏi ReactMarkdown và đặt nó vào div wrapper
  return (
    <div className={`${className} ${themeClasses.text}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeRaw, rehypeKatex]}
        // @ts-expect-error - Bỏ qua lỗi TypeScript cho components
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
