"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Upload, AlertTriangle, FileDown } from "lucide-react";
import { toast } from "sonner";
import { interestService } from "@/services/api/interest.service";
import * as XLSX from "xlsx";
import { downloadFile } from "@/lib/file-utils";

interface UploadInterestModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void; // Callback when upload is successful
}

interface SheetData {
  headers: string[];
  rows: any[][];
}

export function UploadInterestModal({
  open,
  onOpenChange,
  onSuccess,
}: UploadInterestModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [excelData, setExcelData] = useState<Record<string, SheetData>>({});
  const [activeSheet, setActiveSheet] = useState<string | null>(null);
  const [sheetNames, setSheetNames] = useState<string[]>([]);

  // Reset state when modal is closed
  useEffect(() => {
    if (!open) {
      setFile(null);
      setExcelData({});
      setActiveSheet(null);
      setSheetNames([]);
    }
  }, [open]);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (uploadedFile: File) => {
    // Check if file is Excel
    const validTypes = [
      "application/vnd.ms-excel",
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ];

    if (!validTypes.includes(uploadedFile.type)) {
      toast.error("Vui lòng chọn file Excel (.xlsx hoặc .xls)");
      return;
    }

    setFile(uploadedFile);
    processExcelFile(uploadedFile);
  };

  const processExcelFile = (file: File) => {
    setIsProcessing(true);

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = e.target?.result;
        if (data) {
          // Read workbook from ArrayBuffer
          const workbook = XLSX.read(data, { type: "array" });
          const sheets = workbook.SheetNames;

          if (sheets.length === 0) {
            toast.error("File Excel không có dữ liệu");
            setIsProcessing(false);
            return;
          }

          const sheetData: Record<string, SheetData> = {};

          // Process each sheet
          sheets.forEach((sheetName) => {
            const worksheet = workbook.Sheets[sheetName];
            const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });

            if (jsonData.length > 0) {
              const headers = jsonData[0] as string[];
              const rows = jsonData.slice(1) as any[][];

              sheetData[sheetName] = {
                headers,
                rows,
              };
            } else {
              sheetData[sheetName] = {
                headers: [],
                rows: [],
              };
            }
          });

          setExcelData(sheetData);
          setSheetNames(sheets);
          setActiveSheet(sheets[0]);
        }
      } catch (error) {
        console.error("Excel parsing error:", error);
        toast.error(
          "Không thể đọc file Excel. Vui lòng kiểm tra lại định dạng file."
        );
      } finally {
        setIsProcessing(false);
      }
    };

    reader.onerror = () => {
      toast.error("Không thể đọc file");
      setIsProcessing(false);
    };

    reader.readAsArrayBuffer(file);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileChange(e.target.files[0]);
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const templateBlob = await interestService.downloadInterestTemplate();
      await downloadFile(templateBlob, "interest_template.xlsx");
      toast.success("Mẫu Excel từ khóa đã được tải xuống");
    } catch (error) {
      console.error("Template download error:", error);
      toast.error("Không thể tải xuống mẫu Excel");
    }
  };

  const handleSubmit = async () => {
    if (!file) {
      toast.error("Vui lòng chọn file Excel để tải lên");
      return;
    }

    try {
      setIsUploading(true);
      await interestService.uploadInterestFile(file);
      toast.success("Tải lên danh sách từ khóa thành công");
      onOpenChange(false);
      if (onSuccess) onSuccess();
    } catch (error) {
      toast.error("Có lỗi xảy ra khi tải lên từ khóa");
      console.error("Upload error:", error);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[80vw] max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="text-xl font-semibold">
            Tải lên danh sách từ khóa
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-hidden flex flex-col">
          {!file ? (
            <div
              className={`border-2 border-dashed rounded-lg p-6 flex flex-col items-center justify-center transition-colors my-4 ${
                dragActive ? "border-blue-500 bg-blue-50" : "border-gray-300"
              }`}
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
            >
              <Upload className="w-10 h-10 mb-2 text-gray-400" />

              <div className="text-center">
                <p className="font-medium">
                  Kéo thả file Excel hoặc nhấp vào đây
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  Chỉ chấp nhận file Excel (.xlsx hoặc .xls)
                </p>
              </div>

              <input
                type="file"
                id="file-upload-interest"
                accept=".xlsx,.xls"
                className="hidden"
                onChange={handleFileSelect}
              />

              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  document.getElementById("file-upload-interest")?.click()
                }
                className="mt-4"
              >
                Chọn file
              </Button>
            </div>
          ) : (
            <div className="flex-1 overflow-hidden flex flex-col mt-4">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <p className="font-medium text-green-600">{file.name}</p>
                  <p className="text-xs text-gray-500">
                    {(file.size / 1024).toFixed(2)} KB
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setFile(null);
                    setExcelData({});
                    setActiveSheet(null);
                    setSheetNames([]);
                    const fileInput = document.getElementById(
                      "file-upload-interest"
                    ) as HTMLInputElement;
                    if (fileInput) fileInput.value = "";
                  }}
                >
                  Xóa file
                </Button>
              </div>

              {isProcessing ? (
                <div className="flex items-center justify-center h-64">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <p>Đang xử lý dữ liệu...</p>
                  </div>
                </div>
              ) : sheetNames.length > 0 ? (
                <div className="flex-1 overflow-hidden flex flex-col">
                  <Tabs
                    value={activeSheet || sheetNames[0]}
                    onValueChange={setActiveSheet}
                    className="flex-1 flex flex-col overflow-hidden"
                  >
                    <TabsList className="mb-2 overflow-x-auto flex-nowrap">
                      {sheetNames.map((sheetName) => (
                        <TabsTrigger
                          key={sheetName}
                          value={sheetName}
                          className="min-w-fit"
                        >
                          {sheetName}
                        </TabsTrigger>
                      ))}
                    </TabsList>

                    {sheetNames.map((sheetName) => (
                      <TabsContent
                        key={sheetName}
                        value={sheetName}
                        className="flex-1 overflow-auto data-[state=active]:flex-1"
                      >
                        {excelData[sheetName] &&
                        excelData[sheetName].headers.length > 0 ? (
                          <div className="border rounded-md overflow-hidden">
                            <div className="overflow-x-auto">
                              <Table>
                                <TableHeader>
                                  <TableRow>
                                    <TableHead className="w-12 border-r sticky top-0 bg-background z-10">
                                      #
                                    </TableHead>
                                    {excelData[sheetName].headers.map(
                                      (header, index) => (
                                        <TableHead
                                          key={index}
                                          className={`${
                                            index <
                                            excelData[sheetName].headers
                                              .length -
                                              1
                                              ? "border-r"
                                              : ""
                                          } sticky top-0 bg-background z-10`}
                                        >
                                          {header}
                                        </TableHead>
                                      )
                                    )}
                                  </TableRow>
                                </TableHeader>
                                <TableBody>
                                  {excelData[sheetName].rows.length === 0 ? (
                                    <TableRow>
                                      <TableCell
                                        colSpan={
                                          excelData[sheetName].headers.length +
                                          1
                                        }
                                        className="text-center py-4 text-gray-500"
                                      >
                                        Không có dữ liệu
                                      </TableCell>
                                    </TableRow>
                                  ) : (
                                    excelData[sheetName].rows.map(
                                      (row, rowIndex) => (
                                        <TableRow key={rowIndex}>
                                          <TableCell className="border-r">
                                            {rowIndex + 1}
                                          </TableCell>
                                          {excelData[sheetName].headers.map(
                                            (_, cellIndex) => (
                                              <TableCell
                                                key={cellIndex}
                                                className={
                                                  cellIndex <
                                                  excelData[sheetName].headers
                                                    .length -
                                                    1
                                                    ? "border-r"
                                                    : ""
                                                }
                                              >
                                                {row[cellIndex] !== undefined
                                                  ? String(row[cellIndex])
                                                  : ""}
                                              </TableCell>
                                            )
                                          )}
                                        </TableRow>
                                      )
                                    )
                                  )}
                                </TableBody>
                              </Table>
                            </div>
                          </div>
                        ) : (
                          <div className="border rounded-md overflow-hidden p-4 text-center text-gray-500">
                            Sheet {sheetName} không có dữ liệu
                          </div>
                        )}
                      </TabsContent>
                    ))}
                  </Tabs>
                </div>
              ) : (
                <div className="border rounded-md overflow-hidden p-4 text-center text-gray-500">
                  Không có dữ liệu để hiển thị
                </div>
              )}
            </div>
          )}

          <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-md flex items-start gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-500 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-amber-800">
              <p className="font-medium mb-1">Định dạng file Excel yêu cầu:</p>
              <ul className="list-disc pl-5 space-y-1">
                <li>
                  Hãy đảm bảo file Excel của bạn có các cột: Nhãn, Các từ khóa,
                  Trạng thái và Mã màu
                </li>
                <li>Mỗi từ khóa cần được nhập đầy đủ thông tin</li>
              </ul>
            </div>
          </div>

          <div className="mt-4 text-center">
            <Button
              variant="link"
              className="text-blue-600 hover:text-blue-800 text-sm flex items-center mx-auto"
              onClick={handleDownloadTemplate}
            >
              <FileDown className="h-4 w-4 mr-1" />
              Tải xuống mẫu Excel
            </Button>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isUploading}
          >
            Hủy
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!file || isUploading || isProcessing}
            className="bg-[#6366F1] hover:bg-[#4F46E5] text-white"
          >
            {isUploading ? "Đang tải lên..." : "Xác nhận"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
