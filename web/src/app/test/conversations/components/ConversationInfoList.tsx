import { Conversation } from "@/types";
import ConversationInfo from "./ConversationInfo";
interface ConversationInfoListProps {
  isLoading: boolean;
  conversations: Conversation[];
  hasNext: boolean;
  setSkip: React.Dispatch<React.SetStateAction<number>>;
  selectedConversation: Conversation | null;
  handleSelectConversation: (conversation: Conversation) => void;
  conversationLimit: number;
}

export default function ConversationInfoList(props: ConversationInfoListProps) {
  return (
    <div
      className="flex-1 overflow-auto"
      onScroll={(e) => {
        const target = e.target as HTMLDivElement;
        // Kiểm tra khi người dùng cuộn gần đến cuối
        if (target.scrollHeight - target.scrollTop - target.clientHeight < 50) {
          // Chỉ tải thêm nếu có dữ liệu tiếp theo và không đang tải
          if (props.hasNext && !props.isLoading) {
            props.setSkip((prev) => prev + props.conversationLimit);
          }
        }
      }}
    >
      {Array.isArray(props.conversations) && props.conversations.length > 0 ? (
        <>
          {props.conversations.map((item, index) => (
            <ConversationInfo
              key={item.id || index}
              item={item}
              onClick={() => props.handleSelectConversation(item)}
              isSelected={props.selectedConversation?.id === item.id}
            />
          ))}
          {props.isLoading && (
            <div className="p-4 text-center text-gray-500">
              <span className="inline-block animate-spin mr-2">⟳</span>
              Đang tải...
            </div>
          )}
        </>
      ) : (
        <div className="flex-1 overflow-auto flex items-center justify-center text-gray-500">
          Chưa có cuộc hội thoại nào
        </div>
      )}
    </div>
  );
}
