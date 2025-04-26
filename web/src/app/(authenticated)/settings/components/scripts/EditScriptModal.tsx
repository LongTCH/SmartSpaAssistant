"use client";

import { useState, useEffect, useRef } from "react";
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
import { Checkbox } from "@/components/ui/checkbox";
import { Script, ScriptData } from "@/types";
import { toast } from "sonner";
import { scriptService } from "@/services/api/script.service";
import { Badge } from "@/components/ui/badge";
import { X } from "lucide-react";

interface EditScriptModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  scriptId: string | null;
  onSuccess?: () => void;
}

export function EditScriptModal({
  open,
  onOpenChange,
  scriptId,
  onSuccess,
}: EditScriptModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showRelatedScriptsDropdown, setShowRelatedScriptsDropdown] =
    useState(false);
  const [scriptData, setScriptData] = useState<
    Script & { related_script_ids?: string[] }
  >({
    id: "",
    name: "",
    description: "",
    solution: "",
    status: "published",
    created_at: "",
    related_script_ids: [],
  });
  const [availableScripts, setAvailableScripts] = useState<Script[]>([]);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Xử lý click outside để đóng dropdown
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setShowRelatedScriptsDropdown(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  // Fetch script data when scriptId changes
  useEffect(() => {
    const fetchScriptData = async () => {
      if (!scriptId || !open) return;

      setIsLoading(true);

      try {
        const script = await scriptService.getScriptById(scriptId);
        if (!script) {
          toast.error("Không tìm thấy kịch bản");
          return;
        }

        // Convert related_scripts to related_script_ids if it exists
        const related_script_ids = script.related_scripts
          ? script.related_scripts.map((relatedScript) => relatedScript.id)
          : [];

        setScriptData({
          ...script,
          related_script_ids,
        });

        // Also fetch all published scripts for the dropdown
        const allScripts = await scriptService.getAllPublishedScripts();
        // Filter out the current script
        setAvailableScripts(allScripts.filter((s) => s.id !== scriptId));
      } catch (error) {
        toast.error("Không thể tải thông tin kịch bản");
      } finally {
        setIsLoading(false);
      }
    };

    fetchScriptData();
  }, [scriptId, open]);

  const handleChange = (field: string, value: string | string[]) => {
    setScriptData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const toggleRelatedScript = (scriptId: string) => {
    setScriptData((prev) => {
      const currentIds = prev.related_script_ids || [];
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
      const currentIds = prev.related_script_ids || [];
      return {
        ...prev,
        related_script_ids: currentIds.filter((id) => id !== scriptId),
      };
    });
  };

  const getScriptById = (id: string): Script | undefined => {
    return availableScripts.find((script) => script.id === id);
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

      if (!scriptId) {
        toast.error("ID kịch bản không hợp lệ");
        setIsSubmitting(false);
        return;
      }

      // Prepare data for the API
      const updateData: ScriptData = {
        name: scriptData.name,
        description: scriptData.description,
        solution: scriptData.solution,
        status: scriptData.status,
        related_script_ids: scriptData.related_script_ids || [],
      };

      // Call API to update script
      await scriptService.updateScript(scriptId, updateData);
      toast.success("Đã cập nhật kịch bản thành công");
      onSuccess?.();
      onOpenChange(false);
    } catch (error) {
      toast.error("Có lỗi xảy ra khi cập nhật kịch bản");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[800px] h-full overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold text-center">
            Chỉnh sửa kịch bản
          </DialogTitle>
        </DialogHeader>

        {isLoading ? (
          <div className="py-8 space-y-4">
            <div className="h-8 bg-gray-200 animate-pulse rounded w-1/3 mx-auto"></div>
            <div className="h-24 bg-gray-200 animate-pulse rounded"></div>
            <div className="h-24 bg-gray-200 animate-pulse rounded"></div>
          </div>
        ) : (
          <div className="space-y-6 py-4 overflow-y-auto flex-grow">
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
              <label className="text-sm font-medium">
                Mô tả: <span className="text-red-500">*</span>
              </label>
              <Textarea
                className="min-h-[100px]"
                placeholder="Khách hàng hỏi về thời gian hoạt động của thẩm mỹ viện"
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
                placeholder="Thời gian hoạt động từ thứ 2 đến thứ 7, lúc 8h đến 22h"
                value={scriptData.solution}
                onChange={(e) => handleChange("solution", e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Kịch bản liên quan:</label>
              <div className="relative" ref={dropdownRef}>
                <div
                  className="flex flex-wrap min-h-10 max-h-24 overflow-y-auto px-3 py-2 border rounded-md gap-1 cursor-pointer"
                  onClick={() => setShowRelatedScriptsDropdown(true)}
                >
                  {scriptData.related_script_ids &&
                  scriptData.related_script_ids.length > 0 ? (
                    scriptData.related_script_ids.map((scriptId) => {
                      const script = getScriptById(scriptId);
                      return script ? (
                        <Badge
                          key={scriptId}
                          className="mb-1 inline-flex bg-blue-100 text-blue-800 border-blue-200"
                        >
                          {script.name}
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-4 w-4 p-0 ml-1 hover:bg-transparent"
                            onClick={(e) => {
                              e.stopPropagation();
                              removeRelatedScript(scriptId);
                            }}
                          >
                            <X className="h-3 w-3" />
                          </Button>
                        </Badge>
                      ) : null;
                    })
                  ) : (
                    <span className="text-sm text-gray-500">
                      Chọn kịch bản liên quan
                    </span>
                  )}
                </div>

                {showRelatedScriptsDropdown && (
                  <div
                    className="absolute z-50 w-full mt-1 bg-white border rounded-md shadow-lg max-h-60 overflow-auto"
                    style={{ bottom: "auto" }}
                  >
                    <div className="p-2">
                      {availableScripts.filter(
                        (script) =>
                          !scriptData.related_script_ids?.includes(script.id)
                      ).length > 0 ? (
                        availableScripts
                          .filter(
                            (script) =>
                              !scriptData.related_script_ids?.includes(
                                script.id
                              )
                          )
                          .map((script) => (
                            <div
                              key={script.id}
                              className="flex items-center px-2 py-2 hover:bg-gray-100 rounded-md cursor-pointer"
                              onClick={() => {
                                toggleRelatedScript(script.id);
                                if (
                                  availableScripts.filter(
                                    (s) =>
                                      !scriptData.related_script_ids?.includes(
                                        s.id
                                      )
                                  ).length === 1
                                ) {
                                  setShowRelatedScriptsDropdown(false);
                                }
                              }}
                            >
                              <Checkbox
                                id={`script-${script.id}`}
                                checked={
                                  scriptData.related_script_ids?.includes(
                                    script.id
                                  ) || false
                                }
                                className="mr-2"
                              />
                              <label
                                htmlFor={`script-${script.id}`}
                                className="flex-1 cursor-pointer text-sm"
                              >
                                {script.name}
                              </label>
                            </div>
                          ))
                      ) : (
                        <div className="px-2 py-2 text-center text-gray-500 text-sm">
                          Không có kịch bản khả dụng
                        </div>
                      )}
                    </div>
                    <div className="p-2 border-t">
                      <Button
                        variant="ghost"
                        className="w-full text-center text-sm py-1"
                        onClick={() => setShowRelatedScriptsDropdown(false)}
                      >
                        Đóng
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        <DialogFooter className="flex-shrink-0 mt-4 pb-2">
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
