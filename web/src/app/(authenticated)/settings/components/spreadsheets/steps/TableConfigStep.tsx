"use client";

import { useEffect } from "react";
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
import { ColumnConfig, ColumnType } from "@/types";
import { toast } from "sonner";

interface TableConfigStepProps {
  columnConfigs: ColumnConfig[];
  updateColumnConfig: (index: number, field: string, value: any) => void;
  excelData: any; // Add excelData prop
  allRows: any[][]; // All rows from 'data' sheet for more accurate type prediction
  setNextEnabled: (enabled: boolean) => void; // Add a prop to control the Next button state
}

// Cập nhật hàm predictColumnType để xử lý tốt hơn các trường ngày tháng
function predictColumnType(data: any[], columnName: string = ""): ColumnType {
  // ID column validation is now handled in UploadStep.
  // Here, we just hint it as Integer if the name is 'id'.
  // The actual strict validation (uniqueness, non-empty) happens before this step.
  if (columnName.toLowerCase() === "id") {
    // Basic check if data looks like integers, but not as strict as UploadStep
    const looksLikeInteger = data.every((value) => {
      if (value === null || value === undefined || String(value).trim() === "")
        return true; // Allow empty for type prediction, UploadStep handles non-empty rule
      if (typeof value === "number" && Number.isInteger(value)) return true;
      if (typeof value === "string" && /^-?\d+$/.test(String(value).trim()))
        return true;
      return false;
    });
    if (looksLikeInteger) {
      return "Integer" as ColumnType;
    }
    // If it doesn't look like an integer here, let it fall through to other type checks
    // or default to String. The critical validation is already done.
  }

  // Kiểm tra kiểu Boolean
  const booleanPattern = data.every(
    (value) =>
      value === true || value === false || value === "TRUE" || value === "FALSE"
  );
  if (booleanPattern) {
    return "Boolean" as ColumnType;
  }

  // Nếu tên cột chứa date/time thì cũng dự đoán là DateTime
  const dateKeywords = ["date", "time", "ngay", "gio", "thoigian"];
  if (
    columnName &&
    dateKeywords.some((keyword) => columnName.toLowerCase().includes(keyword))
  ) {
    return "DateTime" as ColumnType;
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
    return "Integer" as ColumnType;
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
    return "Numeric" as ColumnType;
  }

  // Kiểm tra kiểu Text (văn bản dài)
  const textPattern = data.some(
    (value) => typeof value === "string" && value.length > 255
  );

  if (textPattern) {
    return "Text" as ColumnType;
  }

  // Mặc định là String cho các giá trị chuỗi khác
  return "String" as ColumnType;
}

export function TableConfigStep({
  columnConfigs,
  updateColumnConfig,
  excelData,
  allRows, // Destructure allRows
  setNextEnabled, // Add a prop to control the Next button state
}: TableConfigStepProps & { setNextEnabled: (enabled: boolean) => void }) {
  const validColumnTypes: { value: ColumnType; label: string }[] = [
    { value: "String", label: "String (Văn bản ngắn)" },
    { value: "Text", label: "Text (Văn bản dài)" },
    { value: "Integer", label: "Integer (Số nguyên)" },
    { value: "Numeric", label: "Numeric (Số thập phân)" },
    { value: "DateTime", label: "DateTime (Ngày giờ)" },
    { value: "Boolean", label: "Boolean (True/False)" },
  ];

  useEffect(() => {
    let initialTypesWereMissing = false;
    columnConfigs.forEach((config) => {
      if (!config.column_type) {
        initialTypesWereMissing = true;
      }
    });

    if (
      excelData &&
      excelData.rows &&
      excelData.headers &&
      allRows &&
      allRows.length > 0
    ) {
      const dataRowsForPrediction = allRows.slice(1);
      let hasError = false;

      const predictedConfigs = columnConfigs.map((config, index) => {
        let currentConfigType = config.column_type;
        // If the type was initially undefined/falsy, treat it as "String" for prediction logic below
        if (!currentConfigType) {
          currentConfigType = "String" as ColumnType;
        }

        if (index >= excelData.headers.length) {
          hasError = true;
          return { ...config, column_type: currentConfigType }; // Use current (possibly defaulted String)
        }

        const columnData: Array<any> = dataRowsForPrediction.map(
          (row: any[]) => row[index]
        );

        let predictedType = currentConfigType;
        const isIdColumn = config.column_name.toLowerCase() === "id";

        // Only predict if current type is "String" (either originally or defaulted)
        if (predictedType === "String") {
          if (isIdColumn) {
            // For 'id' column, if UploadStep set it as Integer, it won't be "String" here.
            // If it is "String" (e.g. defaulted from undefined, or column_config had it as String),
            // try to predict it as Integer.
            const idSpecificPrediction = predictColumnType(
              columnData,
              config.column_name
            );
            if (idSpecificPrediction === "Integer") {
              predictedType = "Integer" as ColumnType;
            } // else it remains "String"
          } else {
            predictedType = predictColumnType(columnData, config.column_name);
          }
        } else if (
          isIdColumn &&
          config.column_type !== "Integer" &&
          predictedType !== "Integer"
        ) {
          // This case handles if 'id' came from column_config as non-Integer, or was undefined.
          // We want to ensure it becomes Integer if data allows.
          const idSpecificPrediction = predictColumnType(
            columnData,
            config.column_name
          );
          if (idSpecificPrediction === "Integer") {
            predictedType = "Integer" as ColumnType;
          }
        }

        return { ...config, column_type: predictedType };
      });

      predictedConfigs.forEach((pConfig, index) => {
        // Update if the new type is different from the original prop's type
        if (pConfig.column_type !== columnConfigs[index].column_type) {
          updateColumnConfig(index, "column_type", pConfig.column_type);
        }
      });

      setNextEnabled(!hasError);

      if (hasError) {
        toast.dismiss();
        toast.error("Có lỗi trong cấu hình cột. Vui lòng kiểm tra lại.");
      }
    } else {
      // Prediction data (excelData, allRows) is NOT available.
      // If any types were initially missing, update them to "String".
      if (initialTypesWereMissing) {
        columnConfigs.forEach((config, index) => {
          if (!config.column_type) {
            updateColumnConfig(index, "column_type", "String" as ColumnType);
          }
        });
      }
      // Enable Next if columnConfigs exist, otherwise disable.
      setNextEnabled(columnConfigs && columnConfigs.length > 0);
    }
  }, [excelData, allRows, columnConfigs, updateColumnConfig, setNextEnabled]);

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
        <div className="border rounded-md overflow-y-auto max-h-[400px]">
          {/* Ensure this div enables scrolling */}
          <Table className="w-full table-fixed">
            <TableHeader>
              <TableRow className="bg-slate-50">
                <TableHead className="w-10 border-r">#</TableHead>
                <TableHead className="w-[15%] border-r">Tên cột</TableHead>
                <TableHead className="w-[20%] border-r">Kiểu dữ liệu</TableHead>
                <TableHead className="border-r">Mô tả</TableHead>
                <TableHead className="w-[10%] text-center">Index</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {columnConfigs.map((column, index) => (
                <TableRow key={index}>
                  <TableCell className="align-middle border-r">
                    {index + 1}
                  </TableCell>
                  <TableCell className="align-middle font-medium border-r">
                    {column.column_name}
                  </TableCell>
                  <TableCell className="align-middle border-r">
                    <Select
                      value={column.column_type}
                      onValueChange={(value) =>
                        updateColumnConfig(index, "column_type", value)
                      }
                      disabled={column.column_name.toLowerCase() === "id"}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Chọn kiểu dữ liệu">
                          {column.column_type
                            ? validColumnTypes.find(
                                (type) => type.value === column.column_type
                              )?.label
                            : "Chọn kiểu dữ liệu"}
                        </SelectValue>
                      </SelectTrigger>
                      <SelectContent>
                        {validColumnTypes.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </TableCell>
                  <TableCell className="align-middle border-r">
                    <Textarea
                      value={column.description || ""}
                      onChange={(e) =>
                        updateColumnConfig(index, "description", e.target.value)
                      }
                      placeholder="Mô tả về cột dữ liệu này"
                      className="min-h-[38px] max-h-[150px] resize-y w-full"
                    />
                  </TableCell>
                  <TableCell className="text-center align-middle">
                    <Checkbox
                      checked={
                        column.column_name.toLowerCase() === "id"
                          ? true
                          : column.is_index || false
                      }
                      onCheckedChange={(checked) =>
                        updateColumnConfig(index, "is_index", !!checked)
                      }
                      disabled={column.column_name.toLowerCase() === "id"}
                    />
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
