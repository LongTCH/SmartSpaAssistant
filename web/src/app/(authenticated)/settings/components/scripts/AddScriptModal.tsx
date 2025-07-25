"use client";

import { useState, useEffect } from "react";
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
import { Script, ScriptData } from "@/types";
import { toast } from "sonner";
import { scriptService } from "@/services/api/script.service";
import { RelatedDropdown } from "./RelatedDropdown";

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
    related_script_ids: [],
  });
  const [availableScripts, setAvailableScripts] = useState<Script[]>([]);

  // Fetch available scripts and sheets for the related dropdowns
  useEffect(() => {
    if (open) {
      const fetchData = async () => {
        try {
          const scriptsResponse = await scriptService.getPaginationScript(
            1,
            100,
            "published"
          );

          setAvailableScripts(scriptsResponse.data);
        } catch {
          toast.error(
            "Không thể tải danh sách kịch bản và bảng tính liên quan"
          );
        }
      };

      fetchData();
    } else {
      // Reset scriptData when modal is closed to ensure clean state
      setScriptData({
        name: "",
        description: "",
        solution: "",
        status: "published",
        related_script_ids: [], // Always empty array, never null
      });
    }
  }, [open]);

  const handleChange = (field: keyof ScriptData, value: string | string[]) => {
    setScriptData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const toggleRelatedScript = (scriptId: string) => {
    setScriptData((prev) => {
      const currentIds = prev.related_script_ids || []; // Ensure we have an array
      const newIds = currentIds.includes(scriptId)
        ? currentIds.filter((id) => id !== scriptId)
        : [...currentIds, scriptId];

      return {
        ...prev,
        related_script_ids: newIds,
      };
    });
  };

  const removeRelatedScript = (scriptId: string) => {
    setScriptData((prev) => {
      const currentIds = prev.related_script_ids || []; // Ensure we have an array
      return {
        ...prev,
        related_script_ids: currentIds.filter((id) => id !== scriptId),
      };
    });
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

      // Ensure related_script_ids is always an array, never null
      const submitData: ScriptData = {
        ...scriptData,
        related_script_ids: scriptData.related_script_ids || [],
      };

      await scriptService.createScript(submitData);
      toast.success("Đã thêm kịch bản mới thành công");

      // Call onSuccess callback if provided
      onSuccess?.();
      onOpenChange(false);
    } catch {
      toast.error("Có lỗi xảy ra khi lưu kịch bản");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[800px] h-full overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold text-center">
            Thêm kịch bản
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-6 py-4 overflow-y-auto flex-grow">
          <div className="flex flex-col md:flex-row gap-4 items-start">
            <div className="space-y-2 flex-1">
              <label className="text-sm font-medium">
                Tên: <span className="text-red-500">*</span>
              </label>
              <Input
                placeholder="THỜI GIAN HOẠT ĐỘNG"
                value={scriptData.name}
                onChange={(e) => handleChange("name", e.target.value)}
              />
            </div>

            <div className="space-y-2 md:w-[200px]">
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
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">
              Mô tả: <span className="text-red-500">*</span>
            </label>
            <Textarea
              className="min-h-[100px]"
              placeholder='"Bên mình hoạt động từ mấy giờ đến mấy giờ vậy", "Cho chị hỏi bên mình làm việc thứ mấy"'
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

          <RelatedDropdown
            label="Kịch bản liên quan"
            items={availableScripts}
            selectedIds={scriptData.related_script_ids || []} // Ensure always array
            onToggleItem={toggleRelatedScript}
            onRemoveItem={removeRelatedScript}
            badgeClassName="bg-blue-100 text-blue-800 border-blue-200"
            placeholder="Chọn kịch bản liên quan"
            emptyMessage="Không có kịch bản khả dụng"
          />
        </div>
        <DialogFooter className="flex-shrink-0 mt-4 pb-2">
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
