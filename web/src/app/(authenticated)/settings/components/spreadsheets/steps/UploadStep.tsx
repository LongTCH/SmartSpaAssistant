"use client";

import { useRef, useState } from "react";
import { Upload, LucideFileSpreadsheet, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import * as XLSX from "xlsx";
import { ExcelData } from "@/types";
import { ColumnConfig, ColumnType } from "@/types";

interface UploadStepProps {
  selectedFile: File | null;
  setSelectedFile: (file: File | null) => void;
  setExcelData: (data: ExcelData | null) => void;
  setAllRows: (rows: any[][]) => void;
  setUploadedTableName: (name: string) => void;
  setUploadedTableDescription: (description: string) => void;
  setInitialColumnConfigs: (configs: ColumnConfig[]) => void; // This was correctly added before
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  // Removed setColumnConfigs as it's replaced by setInitialColumnConfigs for the new flow
}

export function UploadStep({
  selectedFile,
  setSelectedFile,
  setExcelData,
  setAllRows,
  setUploadedTableName,
  setUploadedTableDescription,
  setInitialColumnConfigs, // This was correctly added before
  isLoading,
  setIsLoading,
}: UploadStepProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  // Xử lý chọn file (Restored)
  const handleFileChange = (file: File) => {
    if (!file) return;

    const validExts = [
      ".xlsx",
      ".xls",
      ".csv",
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "application/vnd.ms-excel",
      "text/csv",
    ];
    const fileExt = file.name
      .substring(file.name.lastIndexOf("."))
      .toLowerCase();
    const isValidFile =
      validExts.includes(fileExt) || validExts.includes(file.type);

    if (!isValidFile) {
      toast.error("Vui lòng chọn file Excel hoặc CSV (.xlsx, .xls, .csv)");
      return;
    }

    setSelectedFile(file);
    processExcelFile(file);
  };

  const resetStatesOnError = () => {
    setSelectedFile(null);
    setExcelData(null);
    setAllRows([]);
    setUploadedTableName("");
    setUploadedTableDescription("");
    setInitialColumnConfigs([]);
    setIsLoading(false);
  };

  const processExcelFile = async (file: File) => {
    if (!file) return;
    setIsLoading(true);
    toast.dismiss(); // Clear previous toasts

    try {
      const arrayBuffer = await file.arrayBuffer();
      const workbook = XLSX.read(arrayBuffer, { type: "array" });

      // --- 1. Read 'sheet_info' --- (Updated for new header structure)
      const sheetInfoSheet = workbook.Sheets["sheet_info"];
      let tableNameFromSheet = "";
      let tableDescriptionFromSheet = "";
      if (sheetInfoSheet) {
        // Expects headers: ["field", "value"] (lowercase)
        const sheetInfoData = XLSX.utils.sheet_to_json<{
          [key: string]: string;
        }>(sheetInfoSheet);

        for (const row of sheetInfoData) {
          // Access row properties using lowercase keys
          const field = row["field"]?.toString().toLowerCase().trim();
          const value = row["value"]?.toString().trim();

          if (field === "table") {
            tableNameFromSheet = value || "";
          }
          if (field === "description") {
            tableDescriptionFromSheet = value || "";
          }
        }

        if (
          !tableNameFromSheet &&
          !tableDescriptionFromSheet &&
          sheetInfoData.length > 0
        ) {
          // Fallback for old format if new format fails to find table/description
          // This is a basic fallback, might need more robust detection if both formats are common
          const oldFormatData = XLSX.utils.sheet_to_json<any[]>(
            sheetInfoSheet,
            { header: 1 }
          );
          if (
            oldFormatData.length >= 1 &&
            oldFormatData[0][0]?.toString().toLowerCase() === "table"
          ) {
            tableNameFromSheet = oldFormatData[0][1]?.toString() || "";
          }
          if (
            oldFormatData.length >= 2 &&
            oldFormatData[1][0]?.toString().toLowerCase() === "description"
          ) {
            tableDescriptionFromSheet = oldFormatData[1][1]?.toString() || "";
          }
        }

        setUploadedTableName(tableNameFromSheet);
        setUploadedTableDescription(tableDescriptionFromSheet);

        if (!tableNameFromSheet && !tableDescriptionFromSheet) {
          toast.info(
            "Sheet 'sheet_info' được tìm thấy nhưng không chứa thông tin 'table' hoặc 'description' hợp lệ. Tên và mô tả sẽ cần nhập thủ công."
          );
        }
      } else {
        toast.info(
          "Không tìm thấy sheet 'sheet_info'. Tên và mô tả bảng sẽ cần nhập thủ công."
        );
        setUploadedTableName("");
        setUploadedTableDescription("");
      }

      // --- 2. Read 'column_config' --- (New)
      const columnConfigSheet = workbook.Sheets["column_config"];
      let configsFromSheet: ColumnConfig[] = [];
      if (columnConfigSheet) {
        const columnConfigData = XLSX.utils.sheet_to_json<any>(
          columnConfigSheet,
          { header: ["column_name", "column_type", "description", "is_index"] }
        );
        // Skip the header row if sheet_to_json includes it as the first object
        const actualConfigData = columnConfigData.slice(1);

        configsFromSheet = actualConfigData
          .map((row: any) => ({
            column_name: row.column_name?.toString().trim() || "",
            column_type:
              (row.column_type?.toString() as ColumnType) || "String",
            description: row.description?.toString() || "",
            is_index:
              typeof row.is_index === "boolean"
                ? row.is_index
                : row.is_index?.toString().toLowerCase() === "true" ||
                  row.is_index?.toString() === "1",
          }))
          .filter((config) => config.column_name); // Ensure column_name is present
      }
      // No specific warning if 'column_config' is missing, as defaults will be generated from 'data' sheet.

      // --- 3. Read 'data' sheet (main data) ---
      const dataSheetName =
        workbook.SheetNames.find((name) => name.toLowerCase() === "data") ||
        workbook.SheetNames[0];
      const worksheet = workbook.Sheets[dataSheetName];
      if (!worksheet) {
        toast.error(
          "Không tìm thấy sheet 'data' hoặc sheet dữ liệu chính trong file Excel."
        );
        resetStatesOnError();
        return;
      }

      const headers = (
        XLSX.utils.sheet_to_json(worksheet, { header: 1 })[0] as string[]
      )?.map((h) => String(h).trim());
      if (!headers || headers.length === 0) {
        toast.error("Không tìm thấy header trong sheet 'data'.");
        resetStatesOnError();
        return;
      }

      const allRowsData = XLSX.utils.sheet_to_json(worksheet, {
        header: 1,
        blankrows: false,
        defval: "",
      }) as any[][]; // Includes header row

      if (allRowsData.length <= 1) {
        toast.error("Sheet 'data' không có dữ liệu ngoài dòng tiêu đề.");
        resetStatesOnError();
        return;
      }

      // 'id' column validation (from 'data' sheet headers)
      const idColumnName = headers.find((h) => h.toLowerCase() === "id");
      let idColumnIndex = -1;
      if (idColumnName) {
        idColumnIndex = headers.indexOf(idColumnName);
      }

      if (idColumnIndex === -1) {
        toast.error(
          "Cột 'id' không tồn tại trong sheet 'data'. Vui lòng đặt tên cột định danh là 'id'."
        );
        resetStatesOnError();
        return;
      }

      const idColumnData = allRowsData
        .slice(1)
        .map((row) => row[idColumnIndex]);
      const allValidIds = idColumnData.every((value) => {
        if (
          value === null ||
          value === undefined ||
          String(value).trim() === ""
        )
          return false;
        if (typeof value === "number" && Number.isInteger(value)) return true;
        if (typeof value === "string" && /^-?\d+$/.test(String(value).trim()))
          return true;
        return false;
      });

      if (!allValidIds) {
        toast.error(
          "Cột 'id' trong sheet 'data' phải chứa các giá trị số nguyên và không được để trống."
        );
        resetStatesOnError();
        return;
      }

      const uniqueIds = new Set(idColumnData.map((val) => String(val).trim()));
      if (uniqueIds.size !== idColumnData.length) {
        toast.error(
          "Cột 'id' trong sheet 'data' phải chứa các giá trị duy nhất."
        );
        resetStatesOnError();
        return;
      }

      // --- Generate initialColumnConfigs --- (Merge/Prioritize)
      // Priority: 'column_config' sheet > Defaults for 'id' > Generated from 'data' headers
      let finalGeneratedConfigs: ColumnConfig[] = [];

      if (configsFromSheet.length > 0) {
        // If 'column_config' sheet exists, use it as the base
        // Ensure 'id' column from this sheet gets its special properties if not already set
        finalGeneratedConfigs = configsFromSheet.map((config) => {
          if (config.column_name.toLowerCase() === "id") {
            return {
              ...config,
              column_type: "Integer" as ColumnType, // Force type for 'id'
              description: config.description || "Số thứ tự", // Default description if empty
              is_index: true, // Force index for 'id'
            };
          }
          return config;
        });

        // Check if 'id' column from 'data' sheet was in 'column_config' sheet
        const idInSheetConfig = finalGeneratedConfigs.find(
          (c) => c.column_name.toLowerCase() === "id"
        );
        if (!idInSheetConfig && idColumnName) {
          // id exists in data but not in column_config sheet
          finalGeneratedConfigs.push({
            column_name: idColumnName, // Use the exact name from 'data' sheet header
            column_type: "Integer" as ColumnType,
            is_index: true,
            description: "Số thứ tự",
          });
        }
      } else {
        // If no 'column_config' sheet, generate from 'data' sheet headers
        finalGeneratedConfigs = headers.map((header) => {
          const isIdCol = header.toLowerCase() === "id";
          return {
            column_name: header,
            column_type: isIdCol
              ? ("Integer" as ColumnType)
              : ("String" as ColumnType),
            is_index: isIdCol,
            description: isIdCol ? "Số thứ tự" : "",
          };
        });
      }

      setInitialColumnConfigs(finalGeneratedConfigs);

      const previewRows = allRowsData.slice(1, 11); // Data rows only for preview
      setExcelData({ headers, rows: previewRows });
      setAllRows(allRowsData); // Store all rows including header
    } catch {
      toast.error(
        "Đã xảy ra lỗi khi xử lý file Excel. Vui lòng kiểm tra định dạng file và thử lại."
      );
      resetStatesOnError();
    } finally {
      setIsLoading(false);
    }
  };

  // Xử lý kéo file
  const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();

    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  // Xử lý thả file
  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();

    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  // Click vào khu vực drop để chọn file
  const handleClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="space-y-6 p-4">
      <p className="font-medium text-yellow-800 mb-4">
        Tải lên bảng dữ liệu Excel
      </p>

      {/* File upload area */}
      <div
        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-all ${
          dragActive
            ? "border-blue-500 bg-blue-50"
            : "border-gray-300 hover:border-gray-400"
        }`}
        onClick={handleClick}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={(e) =>
            e.target.files && e.target.files[0]
              ? handleFileChange(e.target.files[0])
              : null
          }
          className="hidden"
          accept=".xlsx,.xls,.csv"
        />

        {!selectedFile ? (
          <div className="flex flex-col items-center justify-center py-4">
            <Upload
              className="h-12 w-12 text-gray-400 mb-2"
              strokeWidth={1.5}
            />
            <p className="mb-2 text-lg font-medium">
              Kéo và thả file Excel hoặc nhấn để chọn file
            </p>
            <p className="text-sm text-muted-foreground">
              Hỗ trợ định dạng: .xlsx, .xls, .csv
            </p>
            <Button className="mt-4" type="button">
              Chọn file
            </Button>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-4">
            <LucideFileSpreadsheet
              className="h-12 w-12 text-green-500 mb-2"
              strokeWidth={1.5}
            />
            <p className="mb-2 text-lg font-medium">
              {selectedFile.name}{" "}
              <span className="text-xs text-gray-500">
                ({(selectedFile.size / 1024).toFixed(0)} KB)
              </span>
            </p>
            {isLoading ? (
              <div className="mt-2 flex items-center space-x-2">
                <div className="h-4 w-4 border-t-2 border-blue-500 rounded-full animate-spin"></div>
                <p className="text-sm">Đang xử lý...</p>
              </div>
            ) : (
              <Button
                className="mt-2"
                variant="outline"
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedFile(null);
                  setExcelData(null);
                  setInitialColumnConfigs([]);
                }}
              >
                Đổi file khác
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Guidelines */}
      <div className="bg-amber-50 border border-amber-200 rounded p-4 text-sm flex space-x-3">
        <AlertCircle className="h-5 w-5 text-amber-500 mt-0.5 flex-shrink-0" />
        <div>
          <p className="font-medium text-amber-800 mb-1">
            Yêu cầu định dạng file:
          </p>
          <ul className="text-amber-700 list-disc pl-5 space-y-1">
            <li>Sử dụng file Excel (.xlsx, .xls) hoặc CSV (.csv)</li>
            <li>Hàng đầu tiên phải chứa tên cột (headers) cho dữ liệu</li>
            <li>
              Mỗi cột nên chứa một loại dữ liệu nhất quán (text, số, ngày
              tháng...)
            </li>
            <li>Kiểm tra và làm sạch dữ liệu trước khi tải lên để tránh lỗi</li>
            <li>
              Dữ liệu ngày tháng nên được định dạng nhất quán để dễ dàng phân
              tích
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
