import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { format } from "date-fns";
import { ChevronLeft, ChevronRight, Plus, Trash2 } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { convertUTCToLocal } from "@/lib/helpers";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"; // DialogClose removed as it's not used directly here, Button is used instead.
import { Button } from "@/components/ui/button";

export interface Conversation {
  id: string;
  date: string;
  // Title is now managed in the parent component
  title?: string;
}

interface ConversationSidebarProps {
  conversations: Conversation[];
  currentConversationId: string;
  onConversationSelect: (id: string) => void;
  onNewConversation: (title?: string) => void;
  onDeleteAllConversations: () => void;
  onDeleteConversation: (id: string) => void;
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
  sidebarOpen,
  toggleSidebar,
  isMobile,
}: ConversationSidebarProps) {
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [conversationToDelete, setConversationToDelete] = useState<
    string | null
  >(null);
  const [isDeletingAll, setIsDeletingAll] = useState(false);

  const handleDeleteRequest = (id: string) => {
    setConversationToDelete(id);
    setIsDeletingAll(false);
    setShowDeleteConfirmation(true);
  };

  const handleDeleteAllRequest = () => {
    setIsDeletingAll(true);
    setShowDeleteConfirmation(true);
  };

  const confirmDelete = () => {
    if (isDeletingAll) {
      onDeleteAllConversations();
    } else if (conversationToDelete) {
      onDeleteConversation(conversationToDelete);
    }
    setShowDeleteConfirmation(false);
    setConversationToDelete(null);
    setIsDeletingAll(false);
    if (isMobile && sidebarOpen) {
      // Close sidebar on mobile after confirmation
      toggleSidebar();
    }
  };

  const cancelDelete = () => {
    setShowDeleteConfirmation(false);
    setConversationToDelete(null);
    setIsDeletingAll(false);
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
                    onClick={() => onNewConversation()}
                    className="p-1.5 rounded-md hover:bg-gray-100"
                    title="New Conversation"
                  >
                    <Plus size={16} />
                  </button>
                  <button
                    onClick={handleDeleteAllRequest} // Updated
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
                        <div
                          onClick={() => onConversationSelect(conversation.id)}
                          className={`group w-full text-left p-3 rounded-lg transition-colors cursor-pointer ${
                            currentConversationId === conversation.id
                              ? "bg-indigo-50 text-indigo-700"
                              : "hover:bg-gray-100 text-gray-700"
                          }`}
                          role="button"
                          tabIndex={0}
                          onKeyDown={(e) => {
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
                                  handleDeleteRequest(conversation.id); // Updated
                                }}
                                className="p-1 rounded-md hover:bg-gray-100 text-red-500 mr-1"
                                aria-label={`Delete conversation ${conversation.title}`}
                              >
                                <Trash2 size={14} />
                              </button>
                            </div>
                          </div>{" "}
                          <div className="text-xs text-gray-500 mt-0.5">
                            {format(
                              convertUTCToLocal(conversation.date),
                              "MMM d, yyyy"
                            )}
                          </div>
                        </div>
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
                key="backdrop"
                initial={{ opacity: 0 }}
                animate={{ opacity: 0.5 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black z-20"
                onClick={toggleSidebar}
              ></motion.div>
              <motion.div
                key="sidebar"
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
                          // For mobile, new conversation modal is not used, directly create.
                          // Consider if mobile should also use the modal for consistency.
                          // For now, it directly creates and closes sidebar.
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
                              </div>{" "}
                              <div className="text-xs text-gray-500 mt-0.5">
                                {format(
                                  convertUTCToLocal(conversation.date),
                                  "MMM d, yyyy"
                                )}
                              </div>
                            </button>
                            <button
                              onClick={() =>
                                // Updated to show confirmation
                                handleDeleteRequest(conversation.id)
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
                        handleDeleteAllRequest(); // Updated
                        // toggleSidebar(); // Removed toggleSidebar, let confirmation handle it
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

      {/* Delete Confirmation Modal */}
      <Dialog
        open={showDeleteConfirmation}
        onOpenChange={setShowDeleteConfirmation}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Deletion</DialogTitle>
            <DialogDescription>
              {isDeletingAll
                ? "Are you sure you want to delete all conversations? This action cannot be undone."
                : `Are you sure you want to delete the conversation "${
                    conversations.find((c) => c.id === conversationToDelete)
                      ?.title
                  }"? This action cannot be undone.`}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={cancelDelete}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={confirmDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

export function saveConversation(conversation: Conversation): void {
  try {
    const existingConversationsJson = localStorage.getItem("conversations");
    const conversations: Conversation[] = existingConversationsJson
      ? JSON.parse(existingConversationsJson)
      : [];

    const existingIndex = conversations.findIndex(
      (c: Conversation) => c.id === conversation.id
    );

    // Only store id and date
    const conversationToStore = {
      id: conversation.id,
      date: conversation.date,
    };

    if (existingIndex !== -1) {
      conversations[existingIndex] = conversationToStore;
    } else {
      conversations.push(conversationToStore);
    }
    localStorage.setItem("conversations", JSON.stringify(conversations));
  } catch {}
}

export function loadConversations(): Conversation[] {
  try {
    const conversationsJson = localStorage.getItem("conversations");
    return conversationsJson ? JSON.parse(conversationsJson) : [];
  } catch {
    return [];
  }
}

export function deleteAllConversations(): void {
  try {
    localStorage.removeItem("conversations");
  } catch {}
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
  } catch {}
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

    const lastOpenedId = localStorage.getItem("test-chat-last-opened-id");
    if (lastOpenedId === conversationId) {
      localStorage.removeItem("test-chat-last-opened-id");
    }
  } catch {}
}
