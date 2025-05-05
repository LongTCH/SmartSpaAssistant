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
  setColumnConfigs: (configs: ColumnConfig[]) => void;
  setExcelData: (data: ExcelData | null) => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  setAllRows: (rows: any[][]) => void;
}

export function UploadStep({
  selectedFile,
  setSelectedFile,
  setColumnConfigs,
  setExcelData,
  isLoading,
  setIsLoading,
  setAllRows,
}: UploadStepProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  // Xử lý chọn file
  const handleFileChange = (file: File) => {
    if (!file) return;

    // Kiểm tra định dạng file
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

  // Xử lý file Excel với hiệu suất cải tiến
  const processExcelFile = async (file: File) => {
    if (!file) return;

    setIsLoading(true);

    try {
      const arrayBuffer = await file.arrayBuffer();
      const workbook = XLSX.read(arrayBuffer);

      // Lấy sheet đầu tiên
      const firstSheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[firstSheetName];

      // Lấy header và tổng số hàng
      const ref = worksheet["!ref"];
      if (!ref) {
        toast.error("File không có dữ liệu");
        setIsLoading(false);
        return;
      }

      // Đọc header từ sheet
      const headers = XLSX.utils.sheet_to_json(worksheet, {
        header: 1,
      })[0] as string[];

      // Kiểm tra có header không
      if (!headers || headers.length === 0) {
        toast.error("Không tìm thấy header trong file Excel");
        setIsLoading(false);
        return;
      }

      // Tạo cấu hình cột mặc định
      const columnConfigs = headers.map((header) => ({
        column_name: String(header).trim(),
        column_type: "String" as ColumnType, // Explicitly cast to ColumnType
        is_index: false,
        description: "",
      }));

      // Ensure allRows is cast to the correct type
      const allRows = XLSX.utils.sheet_to_json(worksheet, {
        header: 1,
        blankrows: false,
        defval: "",
      }) as any[][];

      // Prepare preview data (first 10 rows)
      const previewRows = allRows.slice(0, 10) as any[][];

      // Update state with all rows and preview data
      setColumnConfigs(columnConfigs);
      setExcelData({ headers, rows: previewRows });
      setAllRows(allRows);
    } catch (error) {
      toast.error("Có lỗi xảy ra khi xử lý file Excel");
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
                  setColumnConfigs([]);
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
