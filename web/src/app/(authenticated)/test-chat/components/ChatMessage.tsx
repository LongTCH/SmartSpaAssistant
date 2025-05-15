import { Bot, User } from "lucide-react";
import { motion } from "framer-motion";
// marked is imported but not used, consider removing if not needed elsewhere.
// import { marked } from "marked";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { MarkdownContent } from "@/components/markdown-content";
import { Chat, ChatAttachment } from "@/types/conversation"; // Import Chat type
import { AttachmentViewer } from "@/components/attachment-viewer"; // Import AttachmentViewer

interface ChatMessageProps {
  message: Chat; // Changed from Message to Chat
  index: number;
}

export function ChatMessage({ message, index }: ChatMessageProps) {
  const timestamp = new Date(message.created_at).toLocaleString("vi-VN", {
    // Use message.created_at
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  const isSenderClient = message.content.side === "client";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className={`flex ${
        isSenderClient ? "justify-end" : "justify-start" // Use isSenderClient
      }`}
    >
      {!isSenderClient ? ( // Staff/Bot Message (Light Theme) - if side is not 'client'
        <div className="flex items-start space-x-2 max-w-[80%]">
          <Avatar className="w-8 h-8">
            <AvatarImage src="/placeholder.svg?height=40&width=40" />
            <AvatarFallback>AI</AvatarFallback>
          </Avatar>
          <div>
            <div className="bg-gray-200 p-3 rounded-lg shadow-sm">
              <MarkdownContent
                content={message.content.message.text} // Use message.content.message.text
                className="text-sm"
                isDarkTheme={false}
              />
              {message.content.message.attachments &&
                message.content.message.attachments.length > 0 && (
                  <div className="mt-2">
                    <AttachmentViewer
                      attachments={message.content.message.attachments}
                      isDarkTheme={false}
                    />
                  </div>
                )}
            </div>
            <div className="text-xs text-gray-500 mt-1">{timestamp}</div>
          </div>
        </div>
      ) : (
        // Client/User Message (Dark Theme)
        <div className="flex items-start justify-end space-x-2 max-w-[80%] ml-auto">
          <div>
            <div className="bg-indigo-500 p-3 rounded-lg shadow-sm">
              <MarkdownContent
                content={message.content.message.text} // Use message.content.message.text
                className="text-sm"
                isDarkTheme={true}
              />
              {message.content.message.attachments &&
                message.content.message.attachments.length > 0 && (
                  <div className="mt-2">
                    <AttachmentViewer
                      attachments={message.content.message.attachments}
                      isDarkTheme={true}
                    />
                  </div>
                )}
            </div>
            <div className="text-xs text-gray-500 mt-1 text-right">
              {timestamp}
            </div>
          </div>
          <Avatar className="w-8 h-8">
            <AvatarImage src="/placeholder.svg?height=32&width=32" />
            <AvatarFallback>U</AvatarFallback>
          </Avatar>
        </div>
      )}
    </motion.div>
  );
}

export function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-start space-x-2 max-w-[80%]"
    >
      <Avatar className="w-8 h-8">
        <AvatarImage src="/placeholder.svg?height=40&width=40" />
        <AvatarFallback>AI</AvatarFallback>
      </Avatar>
      <div className="bg-gray-200 rounded-lg p-3 shadow-sm">
        <div className="flex items-center space-x-2">
          <motion.div
            animate={{ y: [0, -5, 0] }}
            transition={{ repeat: Infinity, duration: 1, delay: 0 }}
            className="w-2 h-2 bg-indigo-400 rounded-full"
          ></motion.div>
          <motion.div
            animate={{ y: [0, -5, 0] }}
            transition={{ repeat: Infinity, duration: 1, delay: 0.2 }}
            className="w-2 h-2 bg-indigo-500 rounded-full"
          ></motion.div>
          <motion.div
            animate={{ y: [0, -5, 0] }}
            transition={{ repeat: Infinity, duration: 1, delay: 0.4 }}
            className="w-2 h-2 bg-indigo-600 rounded-full"
          ></motion.div>
        </div>
      </div>
    </motion.div>
  );
}

export function EmptyChatState({
  onSampleQuestionClick,
}: {
  onSampleQuestionClick: (question: string) => void;
}) {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center p-8">
      <div className="w-16 h-16 rounded-full bg-indigo-100 flex items-center justify-center mb-4">
        <Bot size={32} className="text-indigo-600" />
      </div>
      <h3 className="text-xl font-semibold text-gray-800 mb-2">Bot Test</h3>
      <p className="text-gray-600 max-w-md mb-6">
        Xin chào! Tôi có thể giúp bạn trả lời các câu hỏi và cung cấp thông tin
        hữu ích.
      </p>
      <div className="flex flex-wrap justify-center gap-2 max-w-lg">
        <button
          onClick={() => onSampleQuestionClick("Bạn có thể giúp gì cho tôi?")}
          className="px-4 py-2 border border-indigo-200 rounded-md hover:bg-indigo-50 text-indigo-800"
        >
          Bạn có thể giúp gì cho tôi?
        </button>
        <button
          onClick={() => onSampleQuestionClick("Làm thế nào để đặt lịch?")}
          className="px-4 py-2 border border-indigo-200 rounded-md hover:bg-indigo-50 text-indigo-800"
        >
          Làm thế nào để đặt lịch?
        </button>
        <button
          onClick={() => onSampleQuestionClick("Các dịch vụ có sẵn là gì?")}
          className="px-4 py-2 border border-indigo-200 rounded-md hover:bg-indigo-50 text-indigo-800"
        >
          Các dịch vụ có sẵn là gì?
        </button>
      </div>
    </div>
  );
}
