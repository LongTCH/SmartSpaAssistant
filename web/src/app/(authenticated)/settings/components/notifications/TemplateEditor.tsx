"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Textarea } from "@/components/ui/textarea";

interface TemplateEditorProps {
  value: string;
  onChange: (value: string) => void;
  parameters: Array<{ name: string; type: string; description: string }>;
  className?: string;
}

export function TemplateEditor({
  value,
  onChange,
  parameters,
  className = "",
}: TemplateEditorProps) {
  const editorRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [highlightedContent, setHighlightedContent] = useState("");

  // Function to highlight template variables - wrapped in useCallback
  const highlightTemplateVariables = useCallback(
    (text: string) => {
      let highlighted = text; // Replace all template variables with highlighted versions
      parameters.forEach((param) => {
        const regex = new RegExp(`\\{\\{\\s*${param.name}\\s*\\}\\}`, "g");
        highlighted = highlighted.replace(
          regex,
          `<span class="bg-[#F3E8FF] text-[#9333EA] rounded" style="display:inline-block;">{{ ${param.name} }}</span>`
        );
      });

      // Convert newlines to <br> for HTML display
      highlighted = highlighted.replace(/\n/g, "<br>");

      return highlighted;
    },
    [parameters]
  );

  // Update highlighted content whenever value changes
  useEffect(() => {
    setHighlightedContent(highlightTemplateVariables(value));
  }, [value, highlightTemplateVariables]); // Fix dependency array

  // Sync scroll position between textarea and highlight overlay
  const handleScroll = () => {
    if (editorRef.current && textareaRef.current) {
      editorRef.current.scrollTop = textareaRef.current.scrollTop;
    }
  };
  return (
    <div className={`relative border rounded-md ${className}`}>
      <Textarea
        ref={textareaRef}
        className="min-h-[200px] max-h-[300px] text-sm overflow-y-auto custom-scrollbar resize-none p-4 bg-transparent"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onScroll={handleScroll}
      />
      <div
        ref={editorRef}
        className="absolute top-0 left-0 right-0 bottom-0 pointer-events-none p-4 text-sm overflow-y-auto custom-scrollbar"
        dangerouslySetInnerHTML={{ __html: highlightedContent }}
        style={{
          color: "transparent",
          background: "transparent",
          caretColor: "transparent",
        }}
      />
    </div>
  );
}
