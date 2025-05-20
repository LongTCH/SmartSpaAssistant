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
      {isEditable ? (
        <Input
          type="date"
          value={getSafeDateString(value)}
          className="flex-1 bg-white text-sm"
          onChange={(e) => onInputChange(fieldName, e.target.value)}
        />
      ) : (
        <Input
          value={formatSafeDate(value)}
          placeholder="Chưa có thông tin"
          className="flex-1 bg-gray-50 text-sm"
          readOnly
        />
      )}
    </div>
  );
}
