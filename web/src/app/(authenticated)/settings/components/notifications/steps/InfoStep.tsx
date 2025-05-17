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
import { ColorPicker } from "@/components/color-picker";

interface InfoStepProps {
  name: string;
  setName: (value: string) => void;
  status: "published" | "draft";
  setStatus: (value: "published" | "draft") => void;
  color: string;
  setColor: (value: string) => void;
  description: string;
  setDescription: (value: string) => void;
}

export function InfoStep({
  name,
  setName,
  status,
  setStatus,
  color,
  setColor,
  description,
  setDescription,
}: InfoStepProps) {
  return (
    <div className="space-y-6 p-4">
      <div className="flex flex-col md:flex-row gap-4 items-start">
        <div className="space-y-2 flex-1">
          <label className="text-sm font-medium">
            Nhãn: <span className="text-red-500">*</span>
          </label>
          <Input
            placeholder="đặt hàng"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>
        <div className="space-y-2 md:w-[200px]">
          <label className="text-sm font-medium">Trạng thái:</label>
          <Select
            value={status}
            onValueChange={(value: "published" | "draft") => setStatus(value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Xuất bản" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="published">Xuất bản</SelectItem>
              <SelectItem value="draft">Bản nháp</SelectItem>
            </SelectContent>
          </Select>
        </div>{" "}
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium">Màu sắc:</label>
        <ColorPicker value={color} onChange={setColor} />
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium">
          Trường hợp sử dụng: <span className="text-red-500">*</span>
        </label>
        <Textarea
          className="min-h-[160px]"
          placeholder="Khi khách xác nhận đặt hàng và đã cung cấp đầy đủ thông tin 'Họ tên', 'Số điện thoại', 'Địa chỉ'. Đã có đầy đủ thông tin đơn hàng gồm danh sách sản phẩm, bao gồm tên sản phẩm, số lượng, đơn giá. Đã có tổng giá trị đơn hàng (đã trừ khuyến mãi)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </div>
    </div>
  );
}
