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
    <div className="flex items-center justify-between">
      <div className="w-[120px] font-medium">{label}:</div>
      <div className="flex-1 flex items-center">
        {isEditable ? (
          <Select
            value={value || "unknown"} // Treat null as 'unknown' for the Select component
            onValueChange={(val) => onValueChange(fieldName, val)}
            disabled={!isEditable}
          >
            <SelectTrigger className="flex-1 bg-white">
              <SelectValue placeholder="Chọn giới tính" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="male">Nam</SelectItem>
              <SelectItem value="female">Nữ</SelectItem>
              <SelectItem value="unknown">Không xác định</SelectItem>
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
            className="flex-1 bg-gray-50"
            readOnly
          />
        )}
        <Button
          variant="ghost"
          size="icon"
          className="ml-2 h-8 w-8 text-gray-500"
          onClick={() =>
            isEditable ? onReset(fieldName) : onToggleEdit(fieldName)
          }
        >
          {isEditable ? (
            <RotateCcw className="h-4 w-4" />
          ) : (
            <Edit className="h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  );
}
