"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Info, Save } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { SettingsState } from "@/types";
import { toast } from "sonner";

export function OverviewTab() {
  // Global settings state to manage all form values
  const [settings, setSettings] = useState<SettingsState>({
    autoResponseTime: 10,
    messageCount: 10,
    pronouns: {
      self: "em",
      other: "Anh/Chị",
    },
    reactionMessage: "Dạ quý khách cần em hỗ trợ gì thêm không ạ",
    undefinedQuestions: {
      action: "reply",
      responseMessage:
        "Xin lỗi hiện tại em không có thông tin về việc này, quý khách vui lòng liên hệ trực tiếp nhân viên qua số HOTLINE 0123456789 hoặc quý khách có muốn em báo trực tiếp cho nhân viên (có thể phải chờ) không ạ",
    },
  });

  const [isSaving, setIsSaving] = useState(false);

  const handleSaveChanges = async () => {
    setIsSaving(true);

    try {
      // Here you would call your API to save settings
      // For demonstration, we'll simulate an API call with a timeout
      await new Promise((resolve) => setTimeout(resolve, 1000));

      toast.success("Đã lưu thay đổi thành công!");
    } catch (error) {
      toast.error("Có lỗi xảy ra khi lưu thay đổi!");
    } finally {
      setIsSaving(false);
    }
  };

  // Handle form field changes
  const updateSettings = (path: string, value: any) => {
    const pathArray = path.split(".");
    setSettings((prevSettings) => {
      const newSettings = { ...prevSettings };
      let current: any = newSettings;

      // Navigate to the nested property
      for (let i = 0; i < pathArray.length - 1; i++) {
        current = current[pathArray[i]];
      }

      // Update the value
      current[pathArray[pathArray.length - 1]] = value;
      return newSettings;
    });
  };

  return (
    <TooltipProvider>
      <div className="max-w-4xl">
        {/* Sticky header with title and save button */}
        <div className="sticky top-0 z-10 bg-background pt-2 pb-4 flex justify-between items-center border-b mb-8">
          <h1 className="text-2xl font-bold">TỔNG QUAN</h1>
          <Button
            onClick={handleSaveChanges}
            disabled={isSaving}
            className="bg-[#6366F1] hover:bg-[#4F46E5] text-white"
          >
            {isSaving ? (
              <span className="flex items-center">
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                Đang lưu...
              </span>
            ) : (
              <span className="flex items-center">
                <Save className="h-4 w-4 mr-2" />
                Lưu thay đổi
              </span>
            )}
          </Button>
        </div>

        <div className="space-y-8">
          {/* Auto Response Time */}
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-medium">
                Thời gian nhắn tin tự động (giây)
              </h2>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-5 w-5 rounded-full text-[#6366F1]"
                  >
                    <Info className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Thời gian chờ kể từ tin nhắn cuối của khách hàng</p>
                </TooltipContent>
              </Tooltip>
            </div>
            <div className="flex items-center space-x-2 max-w-xs">
              <Input
                type="number"
                value={settings.autoResponseTime}
                onChange={(e) =>
                  updateSettings("autoResponseTime", e.target.value)
                }
                className="text-center h-10 w-24"
              />
              <span className="text-sm">giây</span>
            </div>
          </div>

          {/* Message Count for Emotion Analysis */}
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-medium">
                Số lượng tin nhắn dùng để đánh giá cảm xúc khách hàng (tin)
              </h2>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-5 w-5 rounded-full text-[#6366F1]"
                  >
                    <Info className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Số lượng tin nhắn gần nhất dùng để phân tích cảm xúc</p>
                </TooltipContent>
              </Tooltip>
            </div>
            <div className="flex items-center space-x-2 max-w-xs">
              <Input
                type="number"
                value={settings.messageCount}
                onChange={(e) => updateSettings("messageCount", e.target.value)}
                className="text-center h-10 w-24"
              />
              <span className="text-sm">tin</span>
            </div>
          </div>

          {/* Pronoun Settings */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-medium">Cài đặt cách xưng/hô</h2>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-5 w-5 rounded-full text-[#6366F1]"
                  >
                    <Info className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Cách AI xưng hô với khách hàng</p>
                </TooltipContent>
              </Tooltip>
            </div>
            <div className="grid grid-cols-2 gap-6 max-w-xl">
              <div className="space-y-2">
                <label className="text-sm font-medium">Xưng</label>
                <Input
                  placeholder="em"
                  value={settings.pronouns.self}
                  onChange={(e) =>
                    updateSettings("pronouns.self", e.target.value)
                  }
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Hô</label>
                <Input
                  placeholder="Anh/Chị"
                  value={settings.pronouns.other}
                  onChange={(e) =>
                    updateSettings("pronouns.other", e.target.value)
                  }
                />
              </div>
            </div>
          </div>

          {/* Message Reaction */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-medium">Tin nhắn reaction</h2>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-5 w-5 rounded-full text-[#6366F1]"
                  >
                    <Info className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Tin nhắn gửi cho khách hàng khi họ bấm Like</p>
                </TooltipContent>
              </Tooltip>
            </div>
            <Textarea
              className="min-h-[100px]"
              placeholder="Dạ quý khách cần em hỗ trợ gì thêm không ạ"
              value={settings.reactionMessage}
              onChange={(e) =>
                updateSettings("reactionMessage", e.target.value)
              }
            />
          </div>

          {/* Actions for Undefined Questions */}
          <div className="space-y-4">
            <h2 className="text-lg font-medium">
              Hành động khi gặp câu hỏi không xác định
            </h2>
            <RadioGroup
              value={settings.undefinedQuestions.action}
              onValueChange={(value) =>
                updateSettings("undefinedQuestions.action", value)
              }
              className="flex items-center space-x-6"
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem id="reply" value="reply" />
                <label
                  htmlFor="reply"
                  className="text-sm font-medium cursor-pointer"
                >
                  Nhập câu trả lời
                </label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem id="notify" value="notify" />
                <label
                  htmlFor="notify"
                  className="text-sm font-medium cursor-pointer"
                >
                  Không trả lời và báo cho quản trị viên
                </label>
              </div>
            </RadioGroup>

            {settings.undefinedQuestions.action === "reply" && (
              <Textarea
                className="min-h-[100px] mt-4"
                placeholder="Xin lỗi hiện tại em không có thông tin về việc này, quý khách vui lòng liên hệ trực tiếp nhân viên qua số HOTLINE 0123456789 hoặc quý khách có muốn em báo trực tiếp cho nhân viên (có thể phải chờ) không ạ"
                value={settings.undefinedQuestions.responseMessage}
                onChange={(e) =>
                  updateSettings(
                    "undefinedQuestions.responseMessage",
                    e.target.value
                  )
                }
              />
            )}
          </div>

          {/* Empty div as padding */}
          <div className="h-32" />
        </div>
      </div>
    </TooltipProvider>
  );
}
