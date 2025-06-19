import React, { useCallback, useRef } from "react";
import { Send } from "lucide-react";

interface ChatInputProps {
  disabled: boolean;
  sendMessage: (message: string) => void;
  placeholder?: string;
  isWebSocketConnected?: boolean;
}

export function ChatInput({
  disabled,
  sendMessage,
  placeholder = "Type your message here...",
  isWebSocketConnected = true,
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const isInputDisabled = disabled || !isWebSocketConnected;
  const isTextareaDisabled = !isWebSocketConnected; // Changed: Textarea only disabled if websocket is not connected
  const inputPlaceholder = !isWebSocketConnected
    ? "Đang kết nối lại..."
    : placeholder;

  const handleSendMessage = useCallback(() => {
    if (
      textareaRef.current &&
      textareaRef.current.value.trim() &&
      !isInputDisabled
    ) {
      sendMessage(textareaRef.current.value);
      textareaRef.current.value = "";
      textareaRef.current.style.height = "auto";
    }
  }, [sendMessage, isInputDisabled]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
      }
    },
    [handleSendMessage]
  );

  const handleInput = useCallback(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`;
    }
  }, []);
  return (
    <div className="p-3 bg-white">
      {" "}
      <div className="bg-gray-50 rounded-lg border flex items-stretch overflow-hidden focus-within:ring-2 focus-within:ring-indigo-300 focus-within:border-indigo-400 transition-all shadow-sm">
        <textarea
          ref={textareaRef}
          placeholder={inputPlaceholder}
          className="py-3 px-4 bg-transparent flex-1 min-h-[48px] max-h-[150px] focus:outline-none resize-none text-sm"
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          disabled={isTextareaDisabled} // Changed: Use isTextareaDisabled for the textarea
          rows={1}
        />
        <button
          onClick={handleSendMessage}
          disabled={isInputDisabled}
          className={`px-4 text-white rounded-tr-lg rounded-br-lg flex-shrink-0 transition-colors flex items-center justify-center ${
            isInputDisabled
              ? "bg-gray-300"
              : "bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700"
          }`}
        >
          <Send size={18} />
        </button>
      </div>
      <div className="text-xs text-center text-gray-400 mt-2">
        Nhấn Enter để gửi, Shift+Enter để xuống dòng
      </div>
    </div>
  );
}
