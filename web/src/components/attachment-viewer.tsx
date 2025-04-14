import React, { useState } from "react";
import { ChatAttachment } from "@/types";
import Image from "next/image";
import { MediaViewer } from "./media-viewer";

interface AttachmentViewerProps {
  attachments: ChatAttachment[];
  className?: string;
  isDarkTheme?: boolean;
}

export function AttachmentViewer({
  attachments,
  className = "",
  isDarkTheme = false,
}: AttachmentViewerProps) {
  const [selectedMedia, setSelectedMedia] = useState<ChatAttachment | null>(
    null
  );
  const [mediaViewerOpen, setMediaViewerOpen] = useState(false);
  const [currentMediaIndex, setCurrentMediaIndex] = useState(0);

  // Lọc các attachment là media (hình ảnh, video)
  const mediaAttachments = attachments.filter(
    (att) => att.type === "image" || att.type === "video"
  );

  const handleMediaClick = (attachment: ChatAttachment, index: number) => {
    // Chỉ mở MediaViewer cho image và video
    if (attachment.type === "image" || attachment.type === "video") {
      setSelectedMedia(attachment);
      // Tìm vị trí của attachment này trong danh sách media (không phải tất cả attachments)
      const mediaIndex = mediaAttachments.findIndex(
        (media) => media.payload?.url === attachment.payload?.url
      );
      setCurrentMediaIndex(mediaIndex !== -1 ? mediaIndex : 0);
      setMediaViewerOpen(true);
    }
  };

  const handleNavigateMedia = (index: number) => {
    setCurrentMediaIndex(index);
    setSelectedMedia(mediaAttachments[index]);
  };

  if (!attachments || attachments.length === 0) {
    return null;
  }

  return (
    <>
      <div className={`attachment-container ${className}`}>
        {attachments.map((attachment, index) => {
          const url = attachment.payload?.url || "";

          switch (attachment.type) {
            case "image":
              return (
                <div
                  key={index}
                  className="relative rounded-lg overflow-hidden my-2 max-w-full cursor-pointer"
                  onClick={() => handleMediaClick(attachment, index)}
                >
                  <div className="group relative">
                    <img
                      src={url}
                      alt="Hình ảnh"
                      className="max-w-full max-h-[300px] object-contain rounded-lg transition-transform hover:scale-[1.01]"
                      loading="lazy"
                    />
                    <div className="absolute inset-0 bg-black opacity-0 group-hover:opacity-10 transition-opacity"></div>
                  </div>
                </div>
              );

            case "video":
              return (
                <div
                  key={index}
                  className="my-2 relative cursor-pointer"
                  onClick={() => handleMediaClick(attachment, index)}
                >
                  <div className="group relative">
                    <video
                      className="max-w-full rounded-lg transition-transform hover:scale-[1.01]"
                      style={{ maxHeight: "300px" }}
                    >
                      <source src={url} />
                      Trình duyệt của bạn không hỗ trợ video này.
                    </video>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="w-12 h-12 rounded-full bg-black/60 flex items-center justify-center">
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          width="24"
                          height="24"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          className="text-white"
                        >
                          <polygon points="5 3 19 12 5 21 5 3"></polygon>
                        </svg>
                      </div>
                    </div>
                    <div className="absolute inset-0 bg-black opacity-0 group-hover:opacity-10 transition-opacity"></div>
                  </div>
                </div>
              );

            case "audio":
              return (
                <div key={index} className="my-2">
                  <audio controls className="w-full">
                    <source src={url} />
                    Trình duyệt của bạn không hỗ trợ audio này.
                  </audio>
                </div>
              );

            case "file":
              // Lấy tên file từ URL
              const fileName = url.split("/").pop() || "Tệp đính kèm";

              return (
                <div
                  key={index}
                  className={`flex items-center gap-2 p-3 rounded-lg border ${
                    isDarkTheme
                      ? "bg-gray-800 border-gray-700"
                      : "bg-gray-50 border-gray-200"
                  } my-2`}
                >
                  <div className="flex-shrink-0">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="24"
                      height="24"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className={
                        isDarkTheme ? "text-gray-400" : "text-gray-600"
                      }
                    >
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                      <polyline points="14 2 14 8 20 8"></polyline>
                      <line x1="16" y1="13" x2="8" y2="13"></line>
                      <line x1="16" y1="17" x2="8" y2="17"></line>
                      <polyline points="10 9 9 9 8 9"></polyline>
                    </svg>
                  </div>
                  <div className="overflow-hidden">
                    <div
                      className={`text-sm truncate ${
                        isDarkTheme ? "text-white" : "text-gray-900"
                      }`}
                    >
                      {fileName}
                    </div>
                    <a
                      href={url}
                      download={fileName}
                      className={`text-xs ${
                        isDarkTheme ? "text-blue-400" : "text-blue-600"
                      } hover:underline`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Tải xuống
                    </a>
                  </div>
                </div>
              );

            default:
              return null;
          }
        })}
      </div>

      {/* Media Viewer for images and videos */}
      {mediaViewerOpen && selectedMedia && (
        <MediaViewer
          attachment={selectedMedia}
          attachments={mediaAttachments}
          isOpen={mediaViewerOpen}
          onClose={() => setMediaViewerOpen(false)}
          currentIndex={currentMediaIndex}
          onNavigate={handleNavigateMedia}
        />
      )}
    </>
  );
}
