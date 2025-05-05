import { Conversation } from "@/types";
import ConversationInfo from "./ConversationInfo";
import { useState, useEffect, useRef, useCallback } from "react";
import { conversationService } from "@/services/api/conversation.service";
import { useApp } from "@/context/app-context";
import { WS_MESSAGES } from "@/lib/constants";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ChatAssignmentType } from "@/types";

interface ConversationInfoListProps {
  selectedConversation: Conversation | null;
  setSelectedConversation: React.Dispatch<
    React.SetStateAction<Conversation | null>
  >;
  handleSelectConversation: (conversation: Conversation) => void;
  onNewMessage?: (conversation: Conversation) => void; // Callback when there's a new message
  unreadConversations?: Set<string>; // Set of conversation IDs with unread messages
}

const conversationLimit = 20;
export default function ConversationInfoList(props: ConversationInfoListProps) {
  // Sử dụng state nội bộ để quản lý conversations
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [hasNext, setHasNext] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [assignedTo, setAssignedTo] = useState<ChatAssignmentType>("all");

  // Sử dụng useRef để theo dõi trạng thái đã tải và prevent duplicate API calls
  const hasInitialFetch = useRef(false);
  const isFetchingRef = useRef(false);
  const prevSkipRef = useRef<number>(-1); // Track previous skip value to avoid duplicate calls
  const throttleTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastScrollTimeRef = useRef<number>(0); // Thời gian cuối cùng xử lý sự kiện scroll
  const scrollThrottleTimeMs = 1000; // Khoảng thời gian tối thiểu giữa các lần gọi API khi scroll (ms)

  // Lưu trữ giá trị filter trước đó để phát hiện thay đổi
  const prevAssignedToRef = useRef<ChatAssignmentType>("all");

  // Use the WebSocket context instead of creating a new connection
  const { registerMessageHandler } = useApp();

  // Wrap fetchConversations in useCallback to stabilize it for dependency arrays
  const fetchConversations = useCallback(
    async (isInitialLoad = false) => {
      // Double check to prevent duplicate API calls
      if (isFetchingRef.current) {
        return;
      }

      // Nếu đang tải, không fetch thêm
      if (isLoading) return;

      try {
        // Sử dụng độ dài của mảng hiện tại làm giá trị skip
        const skip = isInitialLoad ? 0 : conversations.length;

        // Prevent duplicate API calls with the same skip value
        if (skip === prevSkipRef.current && !isInitialLoad) {
          return;
        }

        prevSkipRef.current = skip;
        isFetchingRef.current = true;
        setIsLoading(true);

        const response = await conversationService.getPagingConversation(
          skip,
          conversationLimit,
          assignedTo
        );

        if (response.data.length !== 0) {
          if (isInitialLoad) {
            // First page, replace data
            // Đảm bảo không có ID trùng lặp ngay cả khi tải trang đầu tiên
            const uniqueConversations = Array.from(
              new Map(response.data.map((item) => [item.id, item])).values()
            );
            setConversations(uniqueConversations);

            // Auto-select first conversation on page initialization
            if (!props.selectedConversation && uniqueConversations.length > 0) {
              props.setSelectedConversation(uniqueConversations[0]);
            }
          } else {
            // Next page, append data but avoid duplicates
            setConversations((prevConversations) => {
              // Tạo Map với key là ID để loại bỏ trùng lặp
              const conversationsMap = new Map();

              // Thêm conversations hiện có vào Map
              prevConversations.forEach((conv) => {
                conversationsMap.set(conv.id, conv);
              });

              // Thêm conversations mới, chỉ thêm những ID chưa tồn tại
              response.data.forEach((conv) => {
                if (!conversationsMap.has(conv.id)) {
                  conversationsMap.set(conv.id, conv);
                }
              });

              // Chuyển Map thành mảng
              const combinedConversations = Array.from(
                conversationsMap.values()
              );

              return combinedConversations;
            });
          }
          setHasNext(response.has_next || false);
        } else {
          if (isInitialLoad) {
            setConversations([]);
          }
          setHasNext(false);
        }
      } catch (error) {
      } finally {
        setIsLoading(false);
        isFetchingRef.current = false;
      }
    },
    // Loại bỏ assignedTo từ dependencies để tránh tạo ra hàm mới khi filter thay đổi
    // Sử dụng giá trị hiện tại của assignedTo từ lexical scope
    [
      conversations.length,
      isLoading,
      props.selectedConversation,
      props.setSelectedConversation,
    ]
  );

  // Sử dụng debounce để tránh gọi API quá nhiều lần khi cuộn nhanh
  const debouncedFetchMore = useCallback(() => {
    // Clear any existing timeout
    if (throttleTimeoutRef.current) {
      clearTimeout(throttleTimeoutRef.current);
    }

    // Set a new timeout
    throttleTimeoutRef.current = setTimeout(() => {
      fetchConversations();
      throttleTimeoutRef.current = null;
    }, 300); // Debounce 300ms
  }, [fetchConversations]);

  // Handle scroll-based loading with throttle để tránh gọi API nhiều lần
  const handleScroll = useCallback(
    (e: React.UIEvent<HTMLDivElement>) => {
      const target = e.target as HTMLDivElement;
      // Check when user scrolls near the bottom
      if (target.scrollHeight - target.scrollTop - target.clientHeight < 50) {
        // Kiểm tra thời gian từ lần cuối cùng xử lý scroll để throttle request
        const now = Date.now();

        if (hasNext && !isLoading && !isFetchingRef.current) {
          // Chỉ xử lý nếu đã qua đủ thời gian từ lần cuối
          if (now - lastScrollTimeRef.current > scrollThrottleTimeMs) {
            lastScrollTimeRef.current = now;
            debouncedFetchMore();
          } 
        }
      }
    },
    [debouncedFetchMore, hasNext, isLoading]
  );

  // Initial load effect - tách riêng phần xử lý assignedTo và cải thiện để phát hiện tất cả thay đổi
  useEffect(() => {
    // Xác định có phải filter vừa thay đổi không
    const filterChanged =
      hasInitialFetch.current && prevAssignedToRef.current !== assignedTo;

    // Nếu chưa tải lần đầu hoặc filter vừa thay đổi (bất kỳ giá trị nào)
    if (!hasInitialFetch.current || filterChanged) {
      // Nếu là thay đổi filter và không phải lần đầu, reset danh sách
      if (filterChanged) {
        setConversations([]);
        setHasNext(false);
        prevSkipRef.current = -1;
        lastScrollTimeRef.current = 0;
      }

      // Đánh dấu trạng thái fetching để không gọi API trùng lặp
      if (!isFetchingRef.current) {
        isFetchingRef.current = true;
        setIsLoading(true);

        // Gọi API trực tiếp thay vì qua fetchConversations để tránh vòng lặp
        conversationService
          .getPagingConversation(0, conversationLimit, assignedTo)
          .then((response) => {
            if (response.data.length !== 0) {
              // First page, replace data
              // Đảm bảo không có ID trùng lặp
              const uniqueConversations = Array.from(
                new Map(response.data.map((item) => [item.id, item])).values()
              );
              setConversations(uniqueConversations);

              // Auto-select first conversation on page initialization
              if (
                !props.selectedConversation &&
                uniqueConversations.length > 0
              ) {
                props.setSelectedConversation(uniqueConversations[0]);
              }

              setHasNext(response.has_next || false);
            } else {
              setConversations([]);
              setHasNext(false);
            }
          })
          .catch((error) => {
          })
          .finally(() => {
            setIsLoading(false);
            isFetchingRef.current = false;
            hasInitialFetch.current = true;
            // Cập nhật giá trị filter hiện tại
            prevAssignedToRef.current = assignedTo;
          });
      }
    } else {
      // Vẫn cập nhật giá trị filter trước đó ngay cả khi không fetch
      prevAssignedToRef.current = assignedTo;
    }
  }, [assignedTo, props.selectedConversation, props.setSelectedConversation]);

  // Cleanup timeout khi component unmount
  useEffect(() => {
    return () => {
      if (throttleTimeoutRef.current) {
        clearTimeout(throttleTimeoutRef.current);
      }
    };
  }, []);

  // Handle new conversation from WebSocket
  const handleNewConversation = useCallback(
    (conversation: Conversation) => {
      // Nếu props.onNewMessage được cung cấp, gọi nó
      if (props.onNewMessage) {
        props.onNewMessage(conversation);
      }

      // Cập nhật state nội bộ
      setConversations((prevConversations) => {
        // Check if conversation already exists
        const existingIndex = prevConversations.findIndex(
          (conv) => conv.id === conversation.id
        );

        // Create a new list to update state
        let newConversations = [...prevConversations];

        if (existingIndex !== -1) {
          // If exists, remove from old position
          newConversations.splice(existingIndex, 1);
        }

        // Add new conversation to the top of the list
        newConversations = [conversation, ...newConversations];

        return newConversations;
      });
    },
    [props.onNewMessage]
  );

  // Register WebSocket handler
  useEffect(() => {
    // Register handler for "INBOX" messages
    const unregisterInbox = registerMessageHandler(
      WS_MESSAGES.INBOX,
      (data) => {
        handleNewConversation(data as Conversation);
      }
    );
    const unregisterSentiment = registerMessageHandler(
      WS_MESSAGES.UPDATE_SENTIMENT,
      (data) => {
        const conversation = data as Conversation;

        // Nếu props.onNewMessage được cung cấp, gọi nó để cập nhật từ component cha
        if (props.onNewMessage) {
          props.onNewMessage(conversation);
        }

        // Cập nhật state nội bộ
        setConversations((prevConversations) =>
          prevConversations.map((conv) =>
            conv.id === conversation.id
              ? { ...conv, sentiment: conversation.sentiment }
              : conv
          )
        );
      }
    );

    // Cleanup when component unmounts
    return () => {
      unregisterInbox();
      unregisterSentiment();
    };
  }, [handleNewConversation, props.onNewMessage, registerMessageHandler]);

  // Generate a more robust key for each item
  const generateKey = (item: Conversation) => {
    if (!item) return "no-item";
    return (
      item.id ||
      `conv-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
    );
  };

  return (
    <div className="w-80 border-r flex flex-col bg-white">
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <h3 className="text-sm text-gray-500 mr-2">Phụ trách bởi</h3>
          <Select
            value={assignedTo}
            onValueChange={(value: ChatAssignmentType) => setAssignedTo(value)}
          >
            <SelectTrigger className="h-9 w-[120px]">
              <SelectValue placeholder="Tất cả" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tất cả</SelectItem>
              <SelectItem value="ai">AI</SelectItem>
              <SelectItem value="me">Tôi</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      <div className="flex-1 overflow-auto" onScroll={handleScroll}>
        {Array.isArray(conversations) && conversations.length > 0 ? (
          <>
            {conversations.map((item) => (
              <ConversationInfo
                key={generateKey(item)}
                item={item}
                onClick={() => props.handleSelectConversation(item)}
                isSelected={props.selectedConversation?.id === item.id}
                isUnread={props.unreadConversations?.has(item.id) || false}
              />
            ))}
            {isLoading && (
              <div className="p-4 text-center text-gray-500">
                <span className="inline-block animate-spin mr-2">⟳</span>
                Loading...
              </div>
            )}
          </>
        ) : (
          <div className="flex-1 overflow-auto flex items-center justify-center text-gray-500">
            No conversations yet
          </div>
        )}
      </div>
    </div>
  );
}
