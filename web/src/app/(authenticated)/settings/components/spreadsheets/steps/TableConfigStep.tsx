"use client";

import { useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { AlertCircle } from "lucide-react";
import { ColumnConfig } from "@/types";

interface TableConfigStepProps {
  columnConfigs: ColumnConfig[];
  updateColumnConfig: (index: number, field: string, value: any) => void;
  excelData: any; // Add excelData prop
}

// Cập nhật hàm predictColumnType để xử lý tốt hơn các trường ngày tháng
function predictColumnType(data: any[], columnName: string = ""): string {
  // Kiểm tra kiểu Boolean
  const booleanPattern = data.every(
    (value) =>
      value === true || value === false || value === "TRUE" || value === "FALSE"
  );
  if (booleanPattern) {
    return "Boolean";
  }

  // Nếu tên cột chứa date/time thì cũng dự đoán là DateTime
  const dateKeywords = ["date", "time", "ngay", "gio", "thoigian"];
  if (
    columnName &&
    dateKeywords.some((keyword) => columnName.toLowerCase().includes(keyword))
  ) {
    return "DateTime";
  }

  // Kiểm tra kiểu Integer
  const integerPattern = data.every((value) => {
    if (value === null || value === undefined || value === "") return true;
    if (typeof value === "number" && Number.isInteger(value)) {
      return true;
    }
    if (typeof value === "string" && /^-?\d+$/.test(value)) {
      return true;
    }
    return false;
  });

  if (integerPattern) {
    return "Integer";
  }

  // Kiểm tra kiểu Numeric
  const numericPattern = data.every((value) => {
    if (value === null || value === undefined || value === "") return true;
    if (typeof value === "number") {
      return true;
    }
    if (typeof value === "string" && /^-?\d*\.\d+$/.test(value)) {
      return true;
    }
    return false;
  });

  if (numericPattern) {
    return "Numeric";
  }

  // Kiểm tra kiểu Text (văn bản dài)
  const textPattern = data.some(
    (value) => typeof value === "string" && value.length > 255
  );

  if (textPattern) {
    return "Text";
  }

  // Mặc định là String cho các giá trị chuỗi khác
  return "String";
}

export function TableConfigStep({
  columnConfigs,
  updateColumnConfig,
  excelData,
}: TableConfigStepProps) {
  const validColumnTypes = [
    { value: "String", label: "String (Văn bản ngắn)" },
    { value: "Text", label: "Text (Văn bản dài)" },
    { value: "Integer", label: "Integer (Số nguyên)" },
    { value: "Numeric", label: "Numeric (Số thập phân)" },
    { value: "DateTime", label: "DateTime (Ngày giờ)" },
    { value: "Boolean", label: "Boolean (True/False)" },
  ];

  useEffect(() => {
    if (excelData) {
      // Adjust the sampleRows to exclude the header row
      const sampleRows = excelData.rows.slice(1, 11); // Skip the header row and use the first 10 data rows

      // Update the columnData extraction to exclude the header
      const predictedConfigs = columnConfigs.map((config, index) => {
        const columnData: Array<any> = sampleRows.map(
          (row: Record<number, any>) => row[index]
        );
        const predictedType = predictColumnType(columnData, config.column_name);
        return { ...config, column_type: predictedType };
      });

      // Only update column configs if there are changes
      predictedConfigs.forEach((config, index) => {
        if (config.column_type !== columnConfigs[index].column_type) {
          updateColumnConfig(index, "column_type", config.column_type);
        }
      });
    }
  }, [excelData]); // Remove columnConfigs and updateColumnConfig from dependencies

  return (
    <div className="space-y-6 p-4">
      <p className="font-medium text-yellow-800">Cấu hình cột dữ liệu</p>

      {/* Warning message */}
      <div className="bg-red-50 border border-red-200 rounded p-4 mb-4 text-sm flex items-start space-x-2">
        <AlertCircle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
        <div>
          <p className="font-medium text-red-800 mb-1">Lưu ý quan trọng:</p>
          <ul className="text-red-700 mt-2 list-disc list-inside">
            <li>
              Hãy chọn kiểu dữ liệu phù hợp cho từng cột để đảm bảo dữ liệu được
              hiển thị và phân tích chính xác.
            </li>
            <li>
              Đánh dấu cột nào là cột ID/chỉ mục bằng cách tick vào ô Index. Mỗi
              bảng tính nên có ít nhất một cột Index để phân biệt các bản ghi.
            </li>
          </ul>
        </div>
      </div>

      <div>
        <div className="border rounded-md overflow-hidden">
          <Table>
            {" "}
            <TableHeader>
              <TableRow className="bg-slate-50">
                <TableHead className="w-10">#</TableHead>
                <TableHead className="w-[20%]">Tên cột</TableHead>
                <TableHead className="w-[20%]">Kiểu dữ liệu</TableHead>
                <TableHead className="w-[50%]">Mô tả</TableHead>
                <TableHead className="w-[10%] text-center">Index</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {columnConfigs.map((column, index) => (
                <TableRow key={index}>
                  <TableCell className="align-middle">{index + 1}</TableCell>
                  <TableCell className="align-middle font-medium">
                    {column.column_name}
                  </TableCell>
                  <TableCell className="align-middle">
                    <Select
                      value={column.column_type}
                      onValueChange={(value) =>
                        updateColumnConfig(index, "column_type", value)
                      }
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Chọn kiểu dữ liệu" />
                      </SelectTrigger>
                      <SelectContent>
                        {validColumnTypes.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </TableCell>{" "}
                  <TableCell className="align-middle">
                    <div>
                      <Textarea
                        value={column.description || ""}
                        onChange={(e) =>
                          updateColumnConfig(
                            index,
                            "description",
                            e.target.value
                          )
                        }
                        placeholder="Mô tả về cột dữ liệu này"
                        className="min-h-[38px] max-h-[150px] resize-y"
                      />
                    </div>
                  </TableCell>
                  <TableCell className="text-center align-middle">
                    <div className="flex justify-center">
                      <Checkbox
                        checked={column.is_index || false}
                        onCheckedChange={(checked) =>
                          updateColumnConfig(index, "is_index", !!checked)
                        }
                      />
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* Additional help information */}
      <div className="bg-blue-50 border border-blue-200 rounded p-4 text-sm">
        <p className="font-medium text-blue-800 mb-1">
          Hướng dẫn chọn kiểu dữ liệu:
        </p>
        <ul className="text-blue-700 list-disc pl-5 space-y-1">
          <li>
            <strong>String (Văn bản ngắn):</strong> Cho văn bản ngắn, tên, mã
            số...
          </li>
          <li>
            <strong>Text (Văn bản dài):</strong> Cho nội dung dài, ghi chú, mô
            tả...
          </li>
          <li>
            <strong>Integer (Số nguyên):</strong> Cho số nguyên như số lượng, ID
            số...
          </li>
          <li>
            <strong>Numeric (Số thập phân):</strong> Cho giá trị số có phần thập
            phân như giá cả, tỷ lệ...
          </li>
          <li>
            <strong>DateTime:</strong> Cho ngày tháng, thời gian
          </li>
          <li>
            <strong>Boolean:</strong> Cho giá trị đúng/sai, có/không
          </li>
        </ul>
      </div>
    </div>
  );
}
