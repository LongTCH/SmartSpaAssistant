import { Conversation } from "@/types";
import SentimentConversationInfo from "./SentimentConversationInfo";
import { useState, useEffect, useRef, useCallback } from "react";
import { conversationService } from "@/services/api/conversation.service";
import { useApp } from "@/context/app-context";
import { WS_MESSAGES } from "@/lib/constants";
import { toast } from "sonner";

interface SentimentConversationsProps {
  selectedConversation: Conversation | null;
  setSelectedConversation: React.Dispatch<
    React.SetStateAction<Conversation | null>
  >;
}

export default function SentimentConversations(
  props: SentimentConversationsProps
) {
  const [negativeConversations, setNegativeConversations] = useState<
    Conversation[]
  >([]);
  const [positiveConversations, setPositiveConversations] = useState<
    Conversation[]
  >([]);
  const [negativeLoading, setNegativeLoading] = useState<boolean>(false);
  const [positiveLoading, setPositiveLoading] = useState<boolean>(false);
  const [hasMoreNegative, setHasMoreNegative] = useState<boolean>(true);
  const [hasMorePositive, setHasMorePositive] = useState<boolean>(true);
  const [unreadConversationIds, setUnreadConversationIds] = useState<
    Set<string>
  >(new Set());
  const negativeLimit = 10;
  const positiveLimit = 10;

  // Sử dụng useRef để theo dõi trạng thái đã tải
  const hasInitialFetch = useRef(false);

  const { registerMessageHandler } = useApp();

  const fetchNegativeConversations = useCallback(
    async (isInitialLoad = false) => {
      try {
        // Nếu đang tải, không fetch thêm
        if (negativeLoading) return;

        setNegativeLoading(true);

        // Sử dụng độ dài của mảng hiện tại làm giá trị skip
        const skip = isInitialLoad ? 0 : negativeConversations.length;

        const response =
          await conversationService.getPagingConversationBySentiment(
            skip,
            negativeLimit,
            "negative"
          );

        if (response.data.length !== 0) {
          if (isInitialLoad) {
            // First page, replace data
            setNegativeConversations(response.data);
          } else {
            // Next page, append data
            setNegativeConversations((prevConversations) => [
              ...prevConversations,
              ...response.data,
            ]);
          }
          setHasMoreNegative(response.has_next || false);
        } else {
          if (isInitialLoad) {
            setNegativeConversations([]);
          }
          setHasMoreNegative(false);
        }
      } catch {
        // console.error("Error fetching negative conversations:", error);
        toast.error("Không thể tải cuộc trò chuyện tiêu cực");
        setHasMoreNegative(false);
      } finally {
        setNegativeLoading(false);
      }
    },
    [negativeConversations.length, negativeLoading]
  );

  const fetchPositiveConversations = useCallback(
    async (isInitialLoad = false) => {
      try {
        // Nếu đang tải, không fetch thêm
        if (positiveLoading) return;

        setPositiveLoading(true);

        // Sử dụng độ dài của mảng hiện tại làm giá trị skip
        const skip = isInitialLoad ? 0 : positiveConversations.length;

        const response =
          await conversationService.getPagingConversationBySentiment(
            skip,
            positiveLimit,
            "positive"
          );

        if (response.data.length !== 0) {
          if (isInitialLoad) {
            // First page, replace data
            setPositiveConversations(response.data);
          } else {
            // Next page, append data
            setPositiveConversations((prevConversations) => [
              ...prevConversations,
              ...response.data,
            ]);
          }
          setHasMorePositive(response.has_next || false);
        } else {
          if (isInitialLoad) {
            setPositiveConversations([]);
          }
          setHasMorePositive(false);
        }
      } catch {
        // console.error("Error fetching positive conversations:", error);
        toast.error("Không thể tải cuộc trò chuyện tích cực");
        setHasMorePositive(false);
      } finally {
        setPositiveLoading(false);
      }
    },
    [positiveConversations.length, positiveLoading]
  );

  // Thay thế useEffect cũ bằng useEffect mới với cờ hasInitialFetch
  useEffect(() => {
    // Chỉ gọi API khi chưa tải dữ liệu lần đầu
    if (!hasInitialFetch.current) {
      fetchNegativeConversations(true);
      fetchPositiveConversations(true);
      hasInitialFetch.current = true;
    }
  }, [fetchNegativeConversations, fetchPositiveConversations]); // Changed dependency array to [] to run only once on mount

  // Handler for infinite scroll
  const handleNegativeScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;
    if (
      scrollTop + clientHeight >= scrollHeight - 10 &&
      !negativeLoading &&
      hasMoreNegative
    ) {
      fetchNegativeConversations();
    }
  };

  const handlePositiveScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;
    if (
      scrollTop + clientHeight >= scrollHeight - 10 &&
      !positiveLoading &&
      hasMorePositive
    ) {
      fetchPositiveConversations();
    }
  };

  // Hàm xử lý khi nhận message mới hoặc sentiment update từ websocket
  function handleConversationUpdate(updatedConversation: Conversation) {
    const { sentiment, id } = updatedConversation;

    // Cập nhật danh sách positive
    setPositiveConversations((prev) => {
      // Nếu conversation này đã tồn tại trong danh sách, xóa nó đi trước
      const filtered = prev.filter((c) => c.id !== id);

      // Chỉ thêm vào danh sách positive nếu sentiment là positive
      if (sentiment === "positive") {
        return [updatedConversation, ...filtered];
      }
      return filtered;
    });

    // Cập nhật danh sách negative
    setNegativeConversations((prev) => {
      // Nếu conversation này đã tồn tại trong danh sách, xóa nó đi trước
      const filtered = prev.filter((c) => c.id !== id);

      // Chỉ thêm vào danh sách negative nếu sentiment là negative
      if (sentiment === "negative") {
        return [updatedConversation, ...filtered];
      }
      return filtered;
    });

    // Đánh dấu là chưa đọc
    setUnreadConversationIds((prev) => new Set(prev).add(id));
  }

  // Đảm bảo chỉ còn đoạn sau để lắng nghe websocket:
  useEffect(() => {
    // Lắng nghe message mới (INBOX)
    const unregisterInbox = registerMessageHandler(
      WS_MESSAGES.INBOX,
      (data) => {
        handleConversationUpdate(data as Conversation);
      }
    );
    // Lắng nghe cập nhật sentiment
    const unregisterSentiment = registerMessageHandler(
      WS_MESSAGES.UPDATE_SENTIMENT,
      (data) => {
        handleConversationUpdate(data as Conversation);
      }
    );
    return () => {
      unregisterInbox();
      unregisterSentiment();
    };
  }, [registerMessageHandler]);

  // Khi user click vào conversation để đọc
  function handleReadConversation(item: Conversation) {
    props.setSelectedConversation(item);
    setUnreadConversationIds((prev) => {
      const newSet = new Set(prev);
      newSet.delete(item.id);
      return newSet;
    });
  }

  return (
    <div className="w-72 border-l flex flex-col bg-white">
      <div className="flex flex-col h-full">
        {/* Negative Section */}
        <div className="h-1/2 flex flex-col">
          <div className="p-1 bg-red-500 text-white text-center font-medium">
            Tiêu cực
          </div>
          <div
            className="p-2 space-y-2 overflow-auto h-[calc(100%-40px)]"
            onScroll={handleNegativeScroll}
          >
            {negativeConversations.map((item) => (
              <SentimentConversationInfo
                conversation={item}
                key={item.id}
                onClick={() => handleReadConversation(item)}
                isSelected={props.selectedConversation?.id === item.id}
                isUnread={unreadConversationIds.has(item.id)}
              />
            ))}
            {negativeLoading && (
              <div className="text-center text-xs text-gray-400 py-2">
                Đang tải...
              </div>
            )}
          </div>
        </div>

        {/* Positive Section */}
        <div className="h-1/2 flex flex-col">
          <div className="p-1 bg-green-500 text-white text-center font-medium">
            Tích cực
          </div>
          <div
            className="p-2 space-y-2 overflow-auto h-[calc(100%-40px)]"
            onScroll={handlePositiveScroll}
          >
            {positiveConversations.map((item) => (
              <SentimentConversationInfo
                conversation={item}
                key={item.id}
                onClick={() => handleReadConversation(item)}
                isSelected={props.selectedConversation?.id === item.id}
                isUnread={unreadConversationIds.has(item.id)}
              />
            ))}
            {positiveLoading && (
              <div className="text-center text-xs text-gray-400 py-2">
                Đang tải...
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
