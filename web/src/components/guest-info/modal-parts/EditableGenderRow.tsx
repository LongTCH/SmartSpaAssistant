"use client";

import { Button } from "@/components/ui/button";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Edit, RotateCcw } from "lucide-react";

interface EditableGenderRowProps {
  label: string;
  value: string | null; // 'male', 'female', or null (maps to 'unknown' for Select)
  isEditable: boolean;
  fieldName: "gender";
  onValueChange: (fieldName: "gender", value: string) => void;
  onToggleEdit: (fieldName: "gender") => void;
  onReset: (fieldName: "gender") => void;
}

export function EditableGenderRow({
  label,
  value,
  isEditable,
  fieldName,
  onValueChange,
  onToggleEdit,
  onReset,
}: EditableGenderRowProps) {
  return (
    <div className="flex flex-col space-y-1">
      {" "}
      {/* Changed to flex-col and added space-y-1 */}
      <div className="flex items-center justify-between">
        {" "}
        {/* Wrapper for label and edit button */}
        <label className="font-medium text-sm">{label}:</label>{" "}
        {/* Smaller font for label */}
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 text-gray-500" // Smaller button
          onClick={() =>
            isEditable ? onReset(fieldName) : onToggleEdit(fieldName)
          }
        >
          {isEditable ? (
            <RotateCcw className="h-3.5 w-3.5" /> // Smaller icon
          ) : (
            <Edit className="h-3.5 w-3.5" /> // Smaller icon
          )}
        </Button>
      </div>
      {isEditable ? (
        <Select
          value={value || "unknown"}
          onValueChange={(val) => onValueChange(fieldName, val)}
          disabled={!isEditable}
        >
          <SelectTrigger className="flex-1 bg-white text-sm">
            {" "}
            {/* Smaller font */}
            <SelectValue placeholder="Chọn giới tính" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="male" className="text-sm">
              Nam
            </SelectItem>{" "}
            {/* Smaller font */}
            <SelectItem value="female" className="text-sm">
              Nữ
            </SelectItem>{" "}
            {/* Smaller font */}
            <SelectItem value="unknown" className="text-sm">
              Không xác định
            </SelectItem>{" "}
            {/* Smaller font */}
          </SelectContent>
        </Select>
      ) : (
        <Input
          value={
            value === "male"
              ? "Nam"
              : value === "female"
              ? "Nữ"
              : "Chưa có thông tin"
          }
          className="flex-1 bg-gray-50 text-sm" // Smaller font
          readOnly
        />
      )}
    </div>
  );
}
