"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import * as XLSX from "xlsx";
import { toast } from "sonner";
import { scriptService } from "@/services/api/script.service";

interface UploadScriptModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  selectedFile: File | null;
  onSuccess?: () => void; // Callback when upload is successful
}

export function UploadScriptModal({
  open,
  onOpenChange,
  selectedFile,
  onSuccess,
}: UploadScriptModalProps) {
  const [excelData, setExcelData] = useState<{
    headers: string[];
    rows: any[][];
  } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // For lazy loading
  const [allRows, setAllRows] = useState<any[][]>([]);
  const [visibleRows, setVisibleRows] = useState<any[][]>([]);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const rowsPerPage = 20; // Number of rows to display per batch

  // Read Excel file when it changes
  useEffect(() => {
    if (selectedFile) {
      setIsLoading(true);

      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = e.target?.result;
          if (data) {
            // Read workbook from ArrayBuffer
            const workbook = XLSX.read(data, { type: "array" });
            const sheetName = workbook.SheetNames[0];
            const worksheet = workbook.Sheets[sheetName];

            // Convert to JSON
            const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });

            if (jsonData.length > 0) {
              const headers = jsonData[0] as string[];
              const rows = jsonData.slice(1) as any[][];

              // Store all data
              setAllRows(rows);

              // Display initial batch of rows
              const initialRows = rows.slice(0, rowsPerPage);
              setVisibleRows(initialRows);

              setExcelData({
                headers,
                rows: initialRows,
              });
            } else {
              toast.error("File Excel không có dữ liệu");
            }
          } else {
            toast.error("Không thể đọc dữ liệu từ file");
          }
        } catch (error) {
          toast.error(
            "Không thể đọc file Excel. Vui lòng kiểm tra lại định dạng file."
          );
        } finally {
          setIsLoading(false);
        }
      };

      reader.onerror = () => {
        toast.error("Không thể đọc file");
        setIsLoading(false);
      };

      reader.readAsArrayBuffer(selectedFile);
    }
  }, [selectedFile]);

  // Function to load more data
  const loadMore = () => {
    if (allRows.length > visibleRows.length) {
      setIsLoadingMore(true);

      // Calculate next batch of rows to load
      const nextBatch = allRows.slice(
        visibleRows.length,
        visibleRows.length + rowsPerPage
      );

      // Update displayed data
      const newVisibleRows = [...visibleRows, ...nextBatch];
      setVisibleRows(newVisibleRows);

      if (excelData) {
        setExcelData({
          ...excelData,
          rows: newVisibleRows,
        });
      }

      setIsLoadingMore(false);
    }
  };

  // Handle scroll event to detect when to load more data
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;

    // If scrolled near the bottom (within 20px) and not currently loading data
    if (
      scrollHeight - scrollTop - clientHeight < 20 &&
      !isLoadingMore &&
      allRows.length > visibleRows.length
    ) {
      loadMore();
    }
  };

  // Handle upload submission
  const handleSubmit = async () => {
    if (!selectedFile) {
      toast.error("Không tìm thấy file Excel");
      return;
    }

    setIsSubmitting(true);
    try {
      // Call API to upload file
      await scriptService.uploadScriptFile(selectedFile);

      toast.success("Tải lên kịch bản thành công");

      // Close modal and call success callback if provided
      onOpenChange(false);
      if (onSuccess) onSuccess();
    } catch (error: any) {
      toast.error(
        error?.response?.data?.message || "Có lỗi xảy ra khi tải lên kịch bản"
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[90vw] max-h-screen overflow-auto">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold text-center">
            Tải lên kịch bản
          </DialogTitle>
        </DialogHeader>
        <div
          className="space-y-6 py-4 overflow-y-auto pr-1"
          onScroll={handleScroll}
        >
          <div className="space-y-2">
            <label className="text-sm font-medium">File đã chọn:</label>
            <Input
              value={selectedFile?.name || ""}
              disabled
              className="bg-gray-50"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Dữ liệu kịch bản</label>
            <div className="border rounded-md overflow-hidden">
              {isLoading ? (
                <div className="p-4 text-center">
                  Đang đọc dữ liệu từ file Excel...
                </div>
              ) : excelData ? (
                <div className="flex flex-col">
                  <div
                    className="max-h-[400px] overflow-y-auto"
                    onScroll={handleScroll}
                  >
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-12 border-r sticky top-0 bg-background z-10">
                            #
                          </TableHead>
                          {excelData.headers.map((header, index) => (
                            <TableHead
                              key={index}
                              className={`${
                                index < excelData.headers.length - 1
                                  ? "border-r"
                                  : ""
                              } sticky top-0 bg-background z-10`}
                            >
                              {header}
                            </TableHead>
                          ))}
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {excelData.rows.map((row, rowIndex) => (
                          <TableRow key={rowIndex}>
                            <TableCell className="border-r">
                              {rowIndex + 1}
                            </TableCell>
                            {excelData.headers.map((_, cellIndex) => (
                              <TableCell
                                key={cellIndex}
                                className={
                                  cellIndex < excelData.headers.length - 1
                                    ? "border-r"
                                    : ""
                                }
                              >
                                {row[cellIndex] !== undefined
                                  ? String(row[cellIndex])
                                  : ""}
                              </TableCell>
                            ))}
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>

                  {isLoadingMore && (
                    <div className="p-2 text-center text-sm text-muted-foreground">
                      Đang tải thêm dữ liệu...
                    </div>
                  )}

                  {!isLoadingMore && allRows.length > visibleRows.length && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="mx-auto my-2"
                      onClick={loadMore}
                    >
                      Tải thêm ({allRows.length - visibleRows.length} dòng còn
                      lại)
                    </Button>
                  )}

                  {allRows.length > 0 && (
                    <div className="p-2 text-center text-sm text-muted-foreground">
                      Đang hiển thị {visibleRows.length} / {allRows.length} dòng
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-4 text-center">
                  Không có dữ liệu để hiển thị
                </div>
              )}
            </div>
          </div>
        </div>
        <DialogFooter className="flex-shrink-0">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          <Button
            className="bg-[#6366F1] hover:bg-[#4F46E5] text-white"
            onClick={handleSubmit}
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <span className="flex items-center">
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                Đang tải lên...
              </span>
            ) : (
              "Xác nhận"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
