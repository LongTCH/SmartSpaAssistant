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
    <div className="flex flex-col space-y-1">
      <div className="flex items-center justify-between">
        <label className="font-medium text-sm">{label}:</label>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 text-gray-500"
          onClick={() =>
            isEditable ? onReset(fieldName) : onToggleEdit(fieldName)
          }
        >
          {isEditable ? (
            <RotateCcw className="h-3.5 w-3.5" />
          ) : (
            <Edit className="h-3.5 w-3.5" />
          )}
        </Button>
      </div>
      <Input
        value={value || ""}
        placeholder={placeholder}
        className={`flex-1 text-sm ${!isEditable ? "bg-gray-50" : "bg-white"}`}
        readOnly={!isEditable}
        onChange={(e) => onInputChange(fieldName, e.target.value)}
      />
    </div>
  );
}
