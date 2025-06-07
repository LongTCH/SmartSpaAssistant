import React, { useState, useRef, useEffect, useCallback } from "react";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ChatAttachment } from "@/types";
import { downloadFile } from "@/lib/file-utils";
import {
  X,
  ChevronLeft,
  ChevronRight,
  Download,
  Share2,
  Pause,
  Play,
  VolumeX,
  Volume2,
} from "lucide-react";
import { toast } from "sonner";

interface MediaViewerProps {
  attachment: ChatAttachment;
  attachments?: ChatAttachment[];
  isOpen: boolean;
  onClose: () => void;
  currentIndex?: number;
  onNavigate?: (index: number) => void;
}

export function MediaViewer({
  attachment,
  attachments = [],
  isOpen,
  onClose,
  currentIndex = 0,
  onNavigate,
}: MediaViewerProps) {
  const [isPlaying, setIsPlaying] = useState(true);
  const [isMuted, setIsMuted] = useState(false);

  const mediaRef = useRef<HTMLImageElement | HTMLVideoElement | null>(null);
  const contentRef = useRef<HTMLDivElement | null>(null);

  // Reset state when attachment changes
  useEffect(() => {
    setIsPlaying(true);
  }, [attachment]);

  const navigateToNext = useCallback(() => {
    if (attachments.length > 1 && onNavigate) {
      const nextIndex = (currentIndex + 1) % attachments.length;
      onNavigate(nextIndex);
    }
  }, [attachments.length, currentIndex, onNavigate]);

  const navigateToPrev = useCallback(() => {
    if (attachments.length > 1 && onNavigate) {
      const prevIndex =
        (currentIndex - 1 + attachments.length) % attachments.length;
      onNavigate(prevIndex);
    }
  }, [attachments.length, currentIndex, onNavigate]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      } else if (e.key === "ArrowLeft" && attachments.length > 1) {
        navigateToPrev();
      } else if (e.key === "ArrowRight" && attachments.length > 1) {
        navigateToNext();
      }
    },
    [onClose, attachments.length, navigateToPrev, navigateToNext]
  );

  useEffect(() => {
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, currentIndex, handleKeyDown]);

  const handleDownload = () => {
    if (attachment.payload?.url) {
      const fileName = attachment.payload.url.split("/").pop() || "download";
      downloadFile(attachment.payload.url, fileName).catch(() =>
        toast.error("Lỗi tải file", {
          description: "Không thể tải file về, vui lòng thử lại.",
        })
      );
    }
  };

  const handleShare = () => {
    if (navigator.share && attachment.payload?.url) {
      navigator
        .share({
          title: "Chia sẻ tệp",
          url: attachment.payload.url,
        })
        .catch();
    } else {
      navigator.clipboard.writeText(attachment.payload?.url || "");
      alert("Đã sao chép liên kết vào clipboard");
    }
  };

  const togglePlayPause = () => {
    if (attachment.type === "video" && mediaRef.current) {
      const videoElement = mediaRef.current as HTMLVideoElement;
      if (isPlaying) {
        videoElement.pause();
      } else {
        videoElement.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const toggleMute = () => {
    if (
      (attachment.type === "video" || attachment.type === "audio") &&
      mediaRef.current
    ) {
      const mediaElement = mediaRef.current as
        | HTMLVideoElement
        | HTMLAudioElement;
      mediaElement.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const renderMedia = () => {
    const url = attachment.payload?.url || "";

    switch (attachment.type) {
      case "image":
        return (
          <div className="flex items-center justify-center w-full h-full">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              ref={mediaRef as React.RefObject<HTMLImageElement>}
              src={url}
              alt="Hình ảnh"
              className="w-full h-full object-contain"
            />
          </div>
        );

      case "video":
        return (
          <div className="w-full h-full flex flex-col items-center justify-center">
            <video
              ref={mediaRef as React.RefObject<HTMLVideoElement>}
              src={url}
              className="max-w-full max-h-[85%] object-contain"
              autoPlay={isPlaying}
              muted={isMuted}
              controls={false}
              loop
            />
            <div className="flex items-center justify-center space-x-4 mt-4">
              <Button variant="outline" size="icon" onClick={togglePlayPause}>
                {isPlaying ? <Pause size={20} /> : <Play size={20} />}
              </Button>
              <Button variant="outline" size="icon" onClick={toggleMute}>
                {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
              </Button>
            </div>
          </div>
        );

      default:
        return <div>Không thể hiển thị nội dung này</div>;
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogTitle className="hidden"></DialogTitle>
      <DialogContent ref={contentRef} className="h-[95vh] min-w-[95vw] p-0">
        <div className="relative h-full overflow-hidden">
          {/* Close button */}
          <Button
            className="absolute top-2 right-2 z-10 bg-black/50 hover:bg-black/70 text-white"
            size="icon"
            variant="ghost"
            onClick={onClose}
          >
            <X size={20} />
          </Button>

          {/* Navigation buttons */}
          {attachments.length > 1 && (
            <>
              <Button
                className="absolute left-2 top-1/2 -translate-y-1/2 z-10 bg-black/50 hover:bg-black/70 text-white"
                size="icon"
                variant="ghost"
                onClick={navigateToPrev}
              >
                <ChevronLeft size={24} />
              </Button>
              <Button
                className="absolute right-2 top-1/2 -translate-y-1/2 z-10 bg-black/50 hover:bg-black/70 text-white"
                size="icon"
                variant="ghost"
                onClick={navigateToNext}
              >
                <ChevronRight size={24} />
              </Button>

              <div className="absolute bottom-16 left-1/2 -translate-x-1/2 text-white bg-black/50 px-2 py-1 rounded-full text-sm">
                {currentIndex + 1}/{attachments.length}
              </div>
            </>
          )}

          {/* Main content */}
          <div className="w-full h-full bg-black/90 p-4 flex items-center justify-center">
            {renderMedia()}
          </div>

          {/* Toolbar */}
          <div className="absolute bottom-2 left-1/2 transform -translate-x-1/2 flex space-x-2 bg-black/50 rounded-full px-4 py-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={handleDownload}
              className="text-white hover:bg-black/30"
            >
              <Download size={20} />
            </Button>

            <Button
              variant="ghost"
              size="icon"
              onClick={handleShare}
              className="text-white hover:bg-black/30"
            >
              <Share2 size={20} />
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
