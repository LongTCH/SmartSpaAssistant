"use client";

import { Textarea } from "@/components/ui/textarea";
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
          ? "Bạn có thể cập nhật mô tả cho các cột trong bảng tính."
          : "Cấu hình cột cho bảng tính. Bạn có thể thay đổi tên, kiểu dữ liệu và mô tả cho từng cột."}
      </p>

      <div className="border rounded-md overflow-y-auto max-h-[400px]">
        <Table className="w-full table-fixed">
          <TableHeader>
            <TableRow className="bg-muted">
              <TableHead className="w-[50px] border-r">#</TableHead>
              <TableHead className="w-[15%] border-r">Tên cột</TableHead>
              <TableHead className="w-[20%] border-r">Kiểu dữ liệu</TableHead>
              <TableHead className="border-r">Mô tả</TableHead>
              <TableHead className="w-[100px]">Index</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {columnConfigs.map((config, index) => (
              <TableRow key={index} className="hover:bg-muted/50">
                <TableCell className="border-r">{index + 1}</TableCell>
                <TableCell className="border-r">{config.column_name}</TableCell>
                <TableCell className="border-r">
                  {validColumnTypes.find(
                    (type) => type.value === config.column_type
                  )?.label || config.column_type}
                </TableCell>
                <TableCell className="border-r">
                  <Textarea
                    value={config.description || ""}
                    onChange={(e) =>
                      updateColumnConfig(index, "description", e.target.value)
                    }
                    placeholder="Nhập mô tả cho cột này"
                    className="w-full min-h-[60px] focus-visible:ring-1"
                  />
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
