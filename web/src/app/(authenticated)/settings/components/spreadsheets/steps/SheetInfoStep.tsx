"use client";

import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface SheetInfoStepProps {
  name: string;
  setName: (value: string) => void;
  description: string;
  setDescription: (value: string) => void;
  status: "published" | "draft";
  setStatus: (value: "published" | "draft") => void;
}

export function SheetInfoStep({
  name,
  setName,
  description,
  setDescription,
  status,
  setStatus,
}: SheetInfoStepProps) {
  return (
    <div className="space-y-6 p-4">
      <div className="flex flex-col md:flex-row gap-4 items-start">
        <div className="space-y-2 flex-1">
          <label className="text-sm font-medium">
            Tên: <span className="text-red-500">*</span>
          </label>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Tên bảng tính"
          />
          <p className="text-sm text-muted-foreground">
            Đặt tên ngắn gọn, dễ nhớ cho bảng tính này
          </p>
        </div>

        <div className="space-y-2 md:w-[200px]">
          <label className="text-sm font-medium">Trạng thái:</label>
          <Select value={status} onValueChange={setStatus}>
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
        <label className="text-sm font-medium">
          Mô tả: <span className="text-red-500">*</span>
        </label>
        <Textarea
          className="min-h-[200px]"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Mô tả về nội dung và cách sử dụng bảng tính"
        />
        <p className="text-sm text-muted-foreground">
          Mô tả chi tiết giúp người dùng hiểu rõ nội dung và cách sử dụng bảng
          tính này
        </p>
      </div>
    </div>
  );
}
