"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { ScriptData } from "@/types";
import { toast } from "sonner";
import { scriptService } from "@/services/api/script.service";

interface AddScriptModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function AddScriptModal({
  open,
  onOpenChange,
  onSuccess,
}: AddScriptModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [scriptData, setScriptData] = useState<ScriptData>({
    name: "",
    description: "",
    solution: "",
    status: "published",
  });

  const handleChange = (field: keyof ScriptData, value: string) => {
    setScriptData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);

    try {
      // Validate required fields
      if (!scriptData.name || !scriptData.solution) {
        toast.error("Vui lòng điền đầy đủ thông tin bắt buộc");
        setIsSubmitting(false);
        return;
      }
      await scriptService.createScript(scriptData as ScriptData);
      toast.success("Đã thêm kịch bản mới thành công");

      // Call onSuccess callback if provided
      onSuccess?.();
      onOpenChange(false);
    } catch (error) {
      toast.error("Có lỗi xảy ra khi lưu kịch bản");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[800px]">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold text-center">
            Thêm kịch bản
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-6 py-4 overflow-y-auto">
          <div className="space-y-2">
            <label className="text-sm font-medium">Trạng thái:</label>
            <Select
              value={scriptData.status}
              onValueChange={(value: "published" | "draft") =>
                handleChange("status", value)
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Xuất bản" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="published">Xuất bản</SelectItem>
                <SelectItem value="draft">Bản nháp</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">
              Tên: <span className="text-red-500">*</span>
            </label>
            <Input
              placeholder="THỜI GIAN HOẠT ĐỘNG"
              value={scriptData.name}
              onChange={(e) => handleChange("name", e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Mô tả:</label>
            <Textarea
              className="min-h-[100px]"
              placeholder='Khách hàng hỏi về thời gian hoạt động của thẩm mỹ viện
"Bên mình hoạt động từ mấy giờ đến mấy giờ vậy", "Cho chị hỏi bên mình làm việc thứ mấy"'
              value={scriptData.description}
              onChange={(e) => handleChange("description", e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">
              Hướng dẫn trả lời: <span className="text-red-500">*</span>
            </label>
            <Textarea
              className="min-h-[100px]"
              placeholder="Thời gian hoạt động từ thứ 2 đến thứ 7, lúc 8h đến 22h
Nghỉ chủ nhật và các ngày lễ"
              value={scriptData.solution}
              onChange={(e) => handleChange("solution", e.target.value)}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          <Button
            className="bg-[#6366F1] hover:bg-[#4F46E5] text-white"
            onClick={handleSubmit}
            disabled={isSubmitting}
          >
            {isSubmitting ? (
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
              "Lưu"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
