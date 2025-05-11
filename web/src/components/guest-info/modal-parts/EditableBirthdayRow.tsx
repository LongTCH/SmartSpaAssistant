"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Edit, RotateCcw } from "lucide-react";

interface EditableBirthdayRowProps {
  label: string;
  value: string | null; // ISO date string, or empty/null
  isEditable: boolean;
  fieldName: "birthday";
  onInputChange: (fieldName: "birthday", value: string) => void;
  onToggleEdit: (fieldName: "birthday") => void;
  onReset: (fieldName: "birthday") => void;
  getSafeDateString: (isoDate: string | null | undefined) => string;
  formatSafeDate: (isoDate: string | null | undefined) => string;
}

export function EditableBirthdayRow({
  label,
  value,
  isEditable,
  fieldName,
  onInputChange,
  onToggleEdit,
  onReset,
  getSafeDateString,
  formatSafeDate,
}: EditableBirthdayRowProps) {
  return (
    <div className="flex items-center justify-between">
      <div className="w-[120px] font-medium">{label}:</div>
      <div className="flex-1 flex items-center">
        {isEditable ? (
          <Input
            type="date"
            value={getSafeDateString(value)} // Uses parent's helper for date input format
            className="flex-1 bg-white"
            onChange={(e) => onInputChange(fieldName, e.target.value)}
          />
        ) : (
          <Input
            value={formatSafeDate(value)} // Uses parent's helper for display format
            placeholder="Chưa có thông tin"
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
