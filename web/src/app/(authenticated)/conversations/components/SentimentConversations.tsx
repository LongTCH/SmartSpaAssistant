import { Conversation } from "@/types";
import SentimentConversationInfo from "./SentimentConversationInfo";
import { useState, useEffect, useRef } from "react";
import { conversationService } from "@/services/api/conversation.service";
import { useApp } from "@/context/app-context";
import { WS_MESSAGES } from "@/lib/constants";

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

  const { registerMessageHandler } = useApp();

  // Hàm kiểm tra xem một conversation đã tồn tại trong danh sách chưa
  const isConversationExists = (list: Conversation[], id: string): boolean => {
    return list.some((conversation) => conversation.id === id);
  };

  const fetchNegativeConversations = async () => {
    try {
      // Nếu không còn dữ liệu hoặc đang tải, không fetch thêm
      if (!hasMoreNegative || negativeLoading) return;

      setNegativeLoading(true);

      // Sử dụng độ dài của mảng hiện tại làm giá trị skip
      const skip = negativeConversations.length;

      const response =
        await conversationService.getPagingConversationBySentiment(
          skip,
          negativeLimit,
          "negative"
        );

      // Kiểm tra xem còn dữ liệu để tải không
      setHasMoreNegative(response.has_next || false);

      if (response.data.length === 0) {
        setHasMoreNegative(false);
        setNegativeLoading(false);
        return;
      }

      // Chỉ thêm vào những ID chưa tồn tại
      setNegativeConversations((prev) => {
        // Lọc ra những conversation có ID chưa tồn tại trong prev
        const newConversations = response.data.filter(
          (newConv) => !isConversationExists(prev, newConv.id)
        );

        // Nếu không có conversation mới nào, có thể đã hết dữ liệu
        if (newConversations.length === 0) {
          setHasMoreNegative(false);
          return prev;
        }

        // Chỉ thêm mới nếu có conversation mới
        return [...prev, ...newConversations];
      });
    } catch (error) {
      setHasMoreNegative(false);
    } finally {
      setNegativeLoading(false);
    }
  };

  const fetchPositiveConversations = async () => {
    try {
      // Nếu không còn dữ liệu hoặc đang tải, không fetch thêm
      if (!hasMorePositive || positiveLoading) return;

      setPositiveLoading(true);

      // Sử dụng độ dài của mảng hiện tại làm giá trị skip
      const skip = positiveConversations.length;

      const response =
        await conversationService.getPagingConversationBySentiment(
          skip,
          positiveLimit,
          "positive"
        );

      // Kiểm tra xem còn dữ liệu để tải không
      setHasMorePositive(response.has_next || false);

      if (response.data.length === 0) {
        setHasMorePositive(false);
        setPositiveLoading(false);
        return;
      }

      // Chỉ thêm vào những ID chưa tồn tại
      setPositiveConversations((prev) => {
        // Lọc ra những conversation có ID chưa tồn tại trong prev
        const newConversations = response.data.filter(
          (newConv) => !isConversationExists(prev, newConv.id)
        );

        // Nếu không có conversation mới nào, có thể đã hết dữ liệu
        if (newConversations.length === 0) {
          setHasMorePositive(false);
          return prev;
        }

        // Chỉ thêm mới nếu có conversation mới
        return [...prev, ...newConversations];
      });
    } catch (error) {
      setHasMorePositive(false);
    } finally {
      setPositiveLoading(false);
    }
  };

  useEffect(() => {
    fetchNegativeConversations();
  }, []);

  useEffect(() => {
    fetchPositiveConversations();
  }, []);

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
