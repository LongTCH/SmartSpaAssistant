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
import { ColorPicker } from "@/components/color-picker";
import { Interest } from "@/types";
import { toast } from "sonner";
import { interestService } from "@/services/api/interest.service";

interface EditKeywordModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  interestId: string | null;
  onSuccess?: () => void;
}

export function EditKeywordModal({
  open,
  onOpenChange,
  interestId,
  onSuccess,
}: EditKeywordModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [interestData, setInterestData] = useState<Partial<Interest>>({
    name: "",
    related_terms: "",
    status: "published",
    color: "#4CAF50", // Default color
  });

  // Fetch interest data when interestId changes
  useEffect(() => {
    const fetchInterestData = async () => {
      if (!interestId || !open) return;

      setIsLoading(true);

      try {
        const interest = await interestService.getInterestById(interestId);
        if (!interest) {
          toast.error("Không tìm thấy nhãn");
          return;
        }
        setInterestData(interest);
      } catch (error) {
        toast.error("Không thể tải thông tin nhãn");
      } finally {
        setIsLoading(false);
      }
    };

    fetchInterestData();
  }, [interestId, open]);

  const handleChange = (field: keyof Interest, value: string) => {
    setInterestData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);

    try {
      // Validate required fields
      if (!interestData.name) {
        toast.error("Vui lòng điền tên nhãn");
        setIsSubmitting(false);
        return;
      }

      if (!interestId) {
        toast.error("ID nhãn không hợp lệ");
        setIsSubmitting(false);
        return;
      }

      // Call API to update interest
      await interestService.updateInterest(
        interestId,
        interestData as Interest
      );
      toast.success("Đã cập nhật nhãn thành công");
      onSuccess?.();
      onOpenChange(false);
    } catch (error) {
      toast.error("Có lỗi xảy ra khi cập nhật nhãn");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold text-center">
            Chỉnh sửa nhãn
          </DialogTitle>
        </DialogHeader>

        {isLoading ? (
          <div className="py-8 space-y-4">
            <div className="h-8 bg-gray-200 animate-pulse rounded w-1/3 mx-auto"></div>
            <div className="h-24 bg-gray-200 animate-pulse rounded"></div>
            <div className="h-24 bg-gray-200 animate-pulse rounded"></div>
          </div>
        ) : (
          <div className="space-y-6 py-4 overflow-y-auto pr-1">
            <div className="flex flex-col md:flex-row gap-4 items-start">
              <div className="space-y-2 flex-1">
                <label className="text-sm font-medium">
                  Nhãn: <span className="text-red-500">*</span>
                </label>
                <Input
                  placeholder="nám"
                  value={interestData.name}
                  onChange={(e) => handleChange("name", e.target.value)}
                />
              </div>

              <div className="space-y-2 md:w-[200px]">
                <label className="text-sm font-medium">Trạng thái:</label>
                <Select
                  value={interestData.status}
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
              <label className="text-sm font-medium">Màu sắc:</label>
              <ColorPicker
                value={interestData.color || ""}
                onChange={(color) => handleChange("color", color)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Mô tả:</label>
              <Textarea
                className="min-h-[120px]"
                placeholder="nám, trị nám, nám mảng, nám đỉnh, chữa nám, nám lâu năm, làm mờ nám"
                value={interestData.related_terms}
                onChange={(e) => handleChange("related_terms", e.target.value)}
              />
            </div>
          </div>
        )}

        <DialogFooter className="flex-shrink-0">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isLoading || isSubmitting}
          >
            Hủy
          </Button>
          <Button
            className="bg-[#6366F1] hover:bg-[#4F46E5] text-white"
            onClick={handleSubmit}
            disabled={isLoading || isSubmitting}
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
                Đang cập nhật...
              </span>
            ) : (
              "Cập nhật"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
