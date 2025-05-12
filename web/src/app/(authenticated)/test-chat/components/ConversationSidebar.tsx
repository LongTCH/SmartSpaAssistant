import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { format } from "date-fns";
import {
  ChevronLeft,
  ChevronRight,
  Plus,
  Trash2,
  Edit2,
  Check,
  X,
} from "lucide-react";
import { Separator } from "@/components/ui/separator";

export interface Conversation {
  id: string;
  title: string;
  date: string;
  messages: any[];
}

interface ConversationSidebarProps {
  conversations: Conversation[];
  currentConversationId: string;
  onConversationSelect: (id: string) => void;
  onNewConversation: (title?: string) => void;
  onDeleteAllConversations: () => void;
  onDeleteConversation: (id: string) => void;
  onUpdateTitle?: (id: string, newTitle: string) => void;
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  isMobile: boolean;
}

export function ConversationSidebar({
  conversations,
  currentConversationId,
  onConversationSelect,
  onNewConversation,
  onDeleteAllConversations,
  onDeleteConversation,
  onUpdateTitle,
  sidebarOpen,
  toggleSidebar,
  isMobile,
}: ConversationSidebarProps) {
  const [editingConversationId, setEditingConversationId] = useState<
    string | null
  >(null);
  const [newTitle, setNewTitle] = useState<string>("");
  const [showNewConversationModal, setShowNewConversationModal] =
    useState(false);

  const handleEditTitle = (conversation: Conversation, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingConversationId(conversation.id);
    setNewTitle(conversation.title);
  };
  const handleSaveTitle = (e: React.FormEvent) => {
    e.preventDefault();
    if (editingConversationId && newTitle.trim()) {
      // Update locally
      updateConversationTitle(editingConversationId, newTitle.trim());

      // Notify parent component if handler provided
      if (onUpdateTitle) {
        onUpdateTitle(editingConversationId, newTitle.trim());
      }
      if (onUpdateTitle) {
        onUpdateTitle(editingConversationId, newTitle.trim());
      }

      setEditingConversationId(null);
    }
  };

  const handleCancelEdit = () => {
    setEditingConversationId(null);
  };

  const handleCreateNewConversation = () => {
    setShowNewConversationModal(true);
    setNewTitle("New conversation");
  };
  const handleStartNewConversation = () => {
    onNewConversation(newTitle.trim() || "New conversation");
    // Reset state
    setShowNewConversationModal(false);
  };

  const handleCancelNewConversation = () => {
    setShowNewConversationModal(false);
  };

  return (
    <>
      {/* Desktop sidebar */}
      {!isMobile && (
        <>
          <div
            className={`fixed top-16 left-0 bottom-0 transition-all duration-300 z-10 ${
              sidebarOpen ? "w-72" : "w-0 opacity-0"
            }`}
          >
            <div className="bg-white border-r h-full overflow-hidden">
              <div className="flex items-center justify-between p-4 border-b">
                <h3 className="font-medium text-gray-800">Conversations</h3>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={handleCreateNewConversation}
                    className="p-1.5 rounded-md hover:bg-gray-100"
                    title="New Conversation"
                  >
                    <Plus size={16} />
                  </button>
                  <button
                    onClick={onDeleteAllConversations}
                    className="p-1.5 rounded-md hover:bg-gray-100 text-red-500"
                    title="Clear All Conversations"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
              <div className="overflow-y-auto h-[calc(100%-57px)]">
                {conversations.length === 0 ? (
                  <div className="p-4 text-center text-gray-500 text-sm">
                    No conversations yet
                  </div>
                ) : (
                  <div className="space-y-1 p-2">
                    {conversations.map((conversation) => (
                      <div
                        key={conversation.id} // Add key prop here
                        className="relative"
                      >
                        {editingConversationId === conversation.id ? (
                          <form
                            onSubmit={handleSaveTitle}
                            className="p-3 bg-white border rounded-lg"
                          >
                            <input
                              type="text"
                              value={newTitle}
                              onChange={(e) => setNewTitle(e.target.value)}
                              className="w-full p-1 border rounded text-sm mb-2 focus:outline-none focus:ring-1 focus:ring-indigo-400"
                              placeholder="Tên cuộc hội thoại"
                              autoFocus
                            />
                            <div className="flex justify-end space-x-2">
                              <button
                                type="button"
                                onClick={handleCancelEdit}
                                className="p-1 rounded-md hover:bg-gray-100 text-gray-500"
                              >
                                <X size={16} />
                              </button>
                              <button
                                type="submit"
                                className="p-1 rounded-md hover:bg-gray-100 text-indigo-600"
                              >
                                <Check size={16} />
                              </button>
                            </div>
                          </form>
                        ) : (
                          <div
                            onClick={() =>
                              onConversationSelect(conversation.id)
                            }
                            className={`group w-full text-left p-3 rounded-lg transition-colors cursor-pointer ${
                              // Added cursor-pointer
                              currentConversationId === conversation.id
                                ? "bg-indigo-50 text-indigo-700"
                                : "hover:bg-gray-100 text-gray-700"
                            }`}
                            role="button" // Added for accessibility
                            tabIndex={0} // Added for accessibility
                            onKeyDown={(e) => {
                              // Added for keyboard accessibility
                              if (e.key === "Enter" || e.key === " ") {
                                e.preventDefault();
                                onConversationSelect(conversation.id);
                              }
                            }}
                          >
                            <div className="flex items-center justify-between">
                              <div className="font-medium truncate">
                                {conversation.title}
                              </div>
                              <div className="flex items-center opacity-0 group-hover:opacity-100 transition-opacity">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    onDeleteConversation(conversation.id);
                                  }}
                                  className="p-1 rounded-md hover:bg-gray-100 text-red-500 mr-1"
                                  aria-label={`Delete conversation ${conversation.title}`}
                                >
                                  <Trash2 size={14} />
                                </button>
                                <button
                                  onClick={(e) =>
                                    handleEditTitle(conversation, e)
                                  }
                                  className="p-1 rounded-md hover:bg-gray-100"
                                  aria-label={`Edit title for ${conversation.title}`}
                                >
                                  <Edit2 size={14} className="text-gray-500" />
                                </button>
                              </div>
                            </div>
                            <div className="text-xs text-gray-500 mt-0.5">
                              {format(
                                new Date(conversation.date),
                                "MMM d, yyyy"
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
          <button
            onClick={toggleSidebar}
            className={`fixed top-24 transition-all duration-300 bg-white shadow-md rounded-r-md p-1.5 border border-l-0 focus:outline-none z-20 ${
              sidebarOpen ? "left-72" : "left-4"
            } hover:bg-gray-50`}
          >
            {sidebarOpen ? (
              <ChevronLeft size={16} />
            ) : (
              <ChevronRight size={16} />
            )}
          </button>
        </>
      )}

      {/* Mobile sidebar */}
      {isMobile && (
        <AnimatePresence>
          {sidebarOpen && (
            <>
              <motion.div
                key="backdrop" // added key for AnimatePresence child
                initial={{ opacity: 0 }}
                animate={{ opacity: 0.5 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black z-20"
                onClick={toggleSidebar}
              ></motion.div>
              <motion.div
                key="sidebar" // added key for AnimatePresence child
                initial={{ x: "-100%" }}
                animate={{ x: 0 }}
                exit={{ x: "-100%" }}
                transition={{ type: "tween" }}
                className="fixed top-0 left-0 bottom-0 w-72 bg-white z-30"
              >
                <div className="flex flex-col h-full">
                  <div className="flex items-center justify-between p-4 border-b">
                    <h3 className="font-medium">Conversations</h3>
                    <button
                      onClick={toggleSidebar}
                      className="p-1.5 rounded-md hover:bg-gray-100"
                    >
                      <ChevronLeft size={16} />
                    </button>
                  </div>
                  <div className="flex-1 overflow-y-auto">
                    <div className="flex items-center justify-between p-2">
                      <button
                        onClick={() => {
                          onNewConversation();
                          toggleSidebar();
                        }}
                        className="flex items-center space-x-2 p-2 rounded-md hover:bg-gray-100 w-full text-left"
                      >
                        <Plus size={16} />
                        <span>New conversation</span>
                      </button>
                    </div>
                    <Separator className="my-2" />
                    {conversations.length === 0 ? (
                      <div className="p-4 text-center text-gray-500 text-sm">
                        No conversations yet
                      </div>
                    ) : (
                      <div className="space-y-1 p-2">
                        {" "}
                        {conversations.map((conversation) => (
                          <div
                            key={conversation.id}
                            className="flex justify-between items-center"
                          >
                            <button
                              onClick={() => {
                                onConversationSelect(conversation.id);
                                toggleSidebar();
                              }}
                              className={`flex-1 text-left p-3 rounded-lg transition-colors ${
                                currentConversationId === conversation.id
                                  ? "bg-indigo-50 text-indigo-700"
                                  : "hover:bg-gray-100 text-gray-700"
                              }`}
                            >
                              <div className="font-medium truncate">
                                {conversation.title}
                              </div>
                              <div className="text-xs text-gray-500 mt-0.5">
                                {format(
                                  new Date(conversation.date),
                                  "MMM d, yyyy"
                                )}
                              </div>
                            </button>
                            <button
                              onClick={() =>
                                onDeleteConversation(conversation.id)
                              }
                              className="p-2 text-red-500"
                              aria-label={`Delete conversation ${conversation.title}`}
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="p-4 border-t">
                    <button
                      onClick={() => {
                        onDeleteAllConversations();
                        toggleSidebar();
                      }}
                      className="flex items-center space-x-2 text-red-500 hover:text-red-600 p-2 w-full justify-center rounded-md hover:bg-red-50"
                    >
                      <Trash2 size={16} />
                      <span>Clear all conversations</span>
                    </button>
                  </div>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>
      )}

      {/* New Conversation Modal */}
      <NewConversationModal
        isOpen={showNewConversationModal}
        onClose={handleCancelNewConversation}
        onSave={handleStartNewConversation}
        initialTitle={newTitle}
        onTitleChange={setNewTitle}
      />
    </>
  );
}

// Modal component for creating new conversation
function NewConversationModal({
  isOpen,
  onClose,
  onSave,
  initialTitle,
  onTitleChange,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSave: () => void;
  initialTitle: string;
  onTitleChange: (title: string) => void;
}) {
  const [title, setTitle] = useState(initialTitle);

  useEffect(() => {
    if (isOpen) {
      setTitle(initialTitle);
    }
  }, [isOpen, initialTitle]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-semibold mb-4">New Conversation</h2>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Conversation Title
          </label>{" "}
          <input
            type="text"
            value={title}
            onChange={(e) => {
              setTitle(e.target.value);
              // Pass the value back to parent component
              onTitleChange(e.target.value);
            }}
            className="w-full p-2 border rounded focus:outline-none focus:ring-1 focus:ring-indigo-400"
            placeholder="Enter a title for your conversation"
            autoFocus
          />
        </div>
        <div className="flex justify-end space-x-2">
          <button
            onClick={onClose}
            className="px-4 py-2 border rounded hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={onSave}
            className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
          >
            Start Conversation
          </button>
        </div>
      </div>
    </div>
  );
}

export function saveConversation(conversation: Conversation): void {
  try {
    // Get existing conversations from localStorage
    const existingConversationsJson = localStorage.getItem("conversations");
    let conversations = existingConversationsJson
      ? JSON.parse(existingConversationsJson)
      : [];

    // Check if the conversation already exists
    const existingIndex = conversations.findIndex(
      (c: Conversation) => c.id === conversation.id
    );

    if (existingIndex !== -1) {
      // Update existing conversation
      conversations[existingIndex] = conversation;
    } else {
      // Add new conversation
      conversations.push(conversation);
    }

    // Save back to localStorage
    localStorage.setItem("conversations", JSON.stringify(conversations));
  } catch (error) {
    console.error("Error saving conversation:", error);
  }
}

export function loadConversations(): Conversation[] {
  try {
    const conversationsJson = localStorage.getItem("conversations");
    return conversationsJson ? JSON.parse(conversationsJson) : [];
  } catch (error) {
    console.error("Error loading conversations:", error);
    return [];
  }
}

export function deleteAllConversations(): void {
  try {
    localStorage.removeItem("conversations");
  } catch (error) {
    console.error("Error deleting all conversations:", error);
  }
}

export function updateConversationTitle(
  conversationId: string,
  newTitle: string
): void {
  try {
    const conversations = loadConversations();
    const conversationIndex = conversations.findIndex(
      (c) => c.id === conversationId
    );

    if (conversationIndex !== -1) {
      conversations[conversationIndex].title = newTitle;
      localStorage.setItem("conversations", JSON.stringify(conversations));
    }
  } catch (error) {
    console.error("Error updating conversation title:", error);
  }
}

export function deleteConversation(conversationId: string): void {
  try {
    const conversations = loadConversations();
    const filteredConversations = conversations.filter(
      (c) => c.id !== conversationId
    );

    localStorage.setItem(
      "conversations",
      JSON.stringify(filteredConversations)
    );

    // If the deleted conversation was the last opened, remove that reference
    const lastOpenedId = localStorage.getItem("test-chat-last-opened-id");
    if (lastOpenedId === conversationId) {
      localStorage.removeItem("test-chat-last-opened-id");
    }
  } catch (error) {
    console.error("Error deleting conversation:", error);
  }
}
