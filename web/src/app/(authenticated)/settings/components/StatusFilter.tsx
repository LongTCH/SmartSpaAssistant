"use client";

import { useState, useMemo, useEffect, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { downloadFile } from "@/lib/file-utils";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Download,
  Upload,
  Plus,
  Pencil,
  Trash2,
  ChevronLeft,
  ChevronRight,
  Filter,
  AlertTriangle,
  FileDown,
  FileUp,
} from "lucide-react";
interface StatusFilterProps {
  status: string;
  handleStatusChange: (status: string) => void;
}

export function StatusFilter({
  status,
  handleStatusChange,
}: StatusFilterProps) {
  return (
    <div className="flex items-center space-x-2">
      <Filter className="h-4 w-4 text-gray-500" />
      <Select value={status} onValueChange={handleStatusChange}>
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Lọc theo trạng thái" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Tất cả</SelectItem>
          <SelectItem value="published">Xuất bản</SelectItem>
          <SelectItem value="draft">Bản nháp</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
