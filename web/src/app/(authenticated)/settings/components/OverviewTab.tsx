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
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { SettingsState } from "@/types/setting";
import { toast } from "sonner";
import { settingsService } from "@/services/api/setting.service";

export function OverviewTab() {
  // Global settings state to manage all form values
  const [settings, setSettings] = useState<SettingsState>({
    CHAT_WAIT_SECONDS: 1,
    SENTIMENT_INTERVAL_CHAT_COUNT: 2,
    FORM_OF_ADDRESS: {
      ME: "Em",
      OTHER: "Quý khách",
    },
    REACTION_MESSAGE: "Dạ quý khách cần em hỗ trợ gì thêm không ạ",
    UNDEFINED_MESSAGE_HANDLER: {
      TYPE: "response",
      MESSAGE:
        "Xin lỗi hiện tại em không có thông tin về việc này, quý khách vui lòng liên hệ trực tiếp nhân viên qua số HOTLINE 0123456789 hoặc quý khách có muốn em báo trực tiếp cho nhân viên không ạ. Nếu báo nhân viên thì mình phải đợi nhân viên kiểm tra và phản hồi ấy ạ.",
    },
  });

  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Load settings on component mount
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const settingsData = await settingsService.getSettings();
        setSettings(settingsData);
      } catch {
        toast.error("Không thể tải cài đặt. Vui lòng thử lại sau!");
      } finally {
        setIsLoading(false);
      }
    };

    loadSettings();
  }, []);

  const handleSaveChanges = async () => {
    setIsSaving(true);

    try {
      await settingsService.updateSettings(settings);
      toast.success("Đã lưu thay đổi thành công!");
    } catch {
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#6366F1] mx-auto"></div>
          <p className="mt-4">Đang tải dữ liệu...</p>
        </div>
      </div>
    );
  }

  return (
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
              value={settings.CHAT_WAIT_SECONDS}
              onChange={(e) =>
                updateSettings("CHAT_WAIT_SECONDS", Number(e.target.value))
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
              value={settings.SENTIMENT_INTERVAL_CHAT_COUNT}
              onChange={(e) =>
                updateSettings(
                  "SENTIMENT_INTERVAL_CHAT_COUNT",
                  Number(e.target.value)
                )
              }
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
                placeholder="Em"
                value={settings.FORM_OF_ADDRESS.ME}
                onChange={(e) =>
                  updateSettings("FORM_OF_ADDRESS.ME", e.target.value)
                }
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Hô</label>
              <Input
                placeholder="Quý khách"
                value={settings.FORM_OF_ADDRESS.OTHER}
                onChange={(e) =>
                  updateSettings("FORM_OF_ADDRESS.OTHER", e.target.value)
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
            value={settings.REACTION_MESSAGE}
            onChange={(e) => updateSettings("REACTION_MESSAGE", e.target.value)}
          />
        </div>

        {/* Actions for Undefined Questions */}
        <div className="space-y-4">
          <h2 className="text-lg font-medium">
            Hành động khi gặp câu hỏi không xác định
          </h2>
          <RadioGroup
            value={settings.UNDEFINED_MESSAGE_HANDLER.TYPE}
            onValueChange={(value) =>
              updateSettings("UNDEFINED_MESSAGE_HANDLER.TYPE", value)
            }
            className="flex items-center space-x-6"
          >
            <div className="flex items-center space-x-2">
              <RadioGroupItem id="response" value="response" />
              <label
                htmlFor="response"
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

          {settings.UNDEFINED_MESSAGE_HANDLER.TYPE === "response" && (
            <Textarea
              className="min-h-[100px] mt-4"
              placeholder="Xin lỗi hiện tại em không có thông tin về việc này..."
              value={settings.UNDEFINED_MESSAGE_HANDLER.MESSAGE}
              onChange={(e) =>
                updateSettings(
                  "UNDEFINED_MESSAGE_HANDLER.MESSAGE",
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
  );
}
