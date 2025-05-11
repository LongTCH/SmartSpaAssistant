"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Edit, RotateCcw } from "lucide-react";

interface EditableInputRowProps {
  label: string;
  value: string | null;
  placeholder: string;
  isEditable: boolean;
  fieldName: "fullname" | "email" | "phone" | "address"; // Specific field names
  onInputChange: (
    fieldName: "fullname" | "email" | "phone" | "address",
    value: string
  ) => void;
  onToggleEdit: (fieldName: "fullname" | "email" | "phone" | "address") => void;
  onReset: (fieldName: "fullname" | "email" | "phone" | "address") => void;
}

export function EditableInputRow({
  label,
  value,
  placeholder,
  isEditable,
  fieldName,
  onInputChange,
  onToggleEdit,
  onReset,
}: EditableInputRowProps) {
  return (
    <div className="flex items-center justify-between">
      <div className="w-[120px] font-medium">{label}:</div>
      <div className="flex-1 flex items-center">
        <Input
          value={value || ""}
          placeholder={placeholder}
          className={`flex-1 ${!isEditable ? "bg-gray-50" : "bg-white"}`}
          readOnly={!isEditable}
          onChange={(e) => onInputChange(fieldName, e.target.value)}
        />
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
