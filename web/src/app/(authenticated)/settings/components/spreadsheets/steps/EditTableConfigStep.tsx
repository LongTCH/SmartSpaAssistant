"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Checkbox } from "@/components/ui/checkbox";
import { ColumnConfig } from "@/types";

interface EditTableConfigStepProps {
  columnConfigs: ColumnConfig[];
  updateColumnConfig: (index: number, field: string, value: any) => void;
  descriptionOnly?: boolean;
}

export function EditTableConfigStep({
  columnConfigs,
  updateColumnConfig,
  descriptionOnly = false,
}: EditTableConfigStepProps) {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);

  const validColumnTypes = [
    { value: "String", label: "String (Văn bản ngắn)" },
    { value: "Text", label: "Text (Văn bản dài)" },
    { value: "Integer", label: "Integer (Số nguyên)" },
    { value: "Numeric", label: "Numeric (Số thập phân)" },
    { value: "DateTime", label: "DateTime (Ngày giờ)" },
    { value: "Boolean", label: "Boolean (True/False)" },
  ];

  return (
    <div className="space-y-4 p-4">
      <p className="text-sm text-muted-foreground">
        {descriptionOnly
          ? "Bạn có thể cập nhật mô tả cho các cột trong bảng tính. Hãy nhấp vào ô mô tả để chỉnh sửa trực tiếp."
          : "Cấu hình cột cho bảng tính. Bạn có thể thay đổi tên, kiểu dữ liệu và mô tả cho từng cột."}
      </p>

      <div className="border rounded-md overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted">
              <TableHead className="w-[50px]">#</TableHead>
              <TableHead>Tên cột</TableHead>
              <TableHead>Kiểu dữ liệu</TableHead>
              <TableHead className="w-[40%]">Mô tả</TableHead>
              <TableHead className="w-[100px]">Index</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {columnConfigs.map((config, index) => (
              <TableRow key={index} className="hover:bg-muted/50">
                <TableCell>{index + 1}</TableCell>
                <TableCell>{config.column_name}</TableCell>
                <TableCell>
                  {validColumnTypes.find(
                    (type) => type.value === config.column_type
                  )?.label || config.column_type}
                </TableCell>
                <TableCell
                  className={`cursor-text ${
                    editingIndex === index ? "p-0" : ""
                  }`}
                  onClick={() => {
                    if (descriptionOnly && editingIndex !== index) {
                      setEditingIndex(index);
                    }
                  }}
                >
                  {editingIndex === index ? (
                    <Input
                      value={config.description || ""}
                      onChange={(e) =>
                        updateColumnConfig(index, "description", e.target.value)
                      }
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          setEditingIndex(null);
                        }
                      }}
                      onBlur={() => setEditingIndex(null)}
                      autoFocus
                      className="w-full border-none focus-visible:ring-1"
                      placeholder="Nhập mô tả cho cột này"
                    />
                  ) : (
                    <span>
                      {config.description
                        ? config.description
                        : "Chưa có mô tả"}
                    </span>
                  )}
                </TableCell>
                <TableCell className="text-center">
                  <div className="flex justify-center">
                    <Checkbox
                      checked={config.is_index || false}
                      disabled={true}
                    />
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {!descriptionOnly && (
        <p className="text-sm text-blue-600 italic">
          * Lưu ý: Chỉ có thể chỉnh sửa mô tả trong chế độ chỉnh sửa bảng tính.
        </p>
      )}
    </div>
  );
}
