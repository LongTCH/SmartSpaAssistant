"use client";

import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";

interface GuestInfoModalActionsProps {
  onCancel: () => void;
  onSave: () => Promise<void>;
  isSaving: boolean;
  canSave: boolean;
}

export function GuestInfoModalActions({
  onCancel,
  onSave,
  isSaving,
  canSave,
}: GuestInfoModalActionsProps) {
  return (
    <div className="flex justify-center gap-4 p-6 pt-2">
      <Button
        variant="outline"
        className="w-24"
        onClick={onCancel}
        disabled={isSaving}
      >
        Hủy
      </Button>
      <Button
        className="w-24 bg-[#6366F1] hover:bg-[#4F46E5]"
        onClick={onSave}
        disabled={isSaving || !canSave}
      >
        {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : "Lưu"}
      </Button>
    </div>
  );
}
