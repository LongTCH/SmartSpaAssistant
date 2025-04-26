"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
import { ExcelData } from "@/types";
import { sheetService } from "@/services/api/sheet.service";

interface AddSpreadsheetModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  selectedFile: File | null;
  onSuccess?: () => void; // Thêm callback khi lưu thành công
}

export function AddSpreadsheetModal({
  open,
  onOpenChange,
  selectedFile,
  onSuccess,
}: AddSpreadsheetModalProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState("published");
  const [excelData, setExcelData] = useState<ExcelData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // New state variables for lazy loading
  const [allRows, setAllRows] = useState<any[][]>([]);
  const [visibleRows, setVisibleRows] = useState<any[][]>([]);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const rowsPerPage = 20; // Số dòng hiển thị mỗi lần tải thêm

  // Read Excel file when it changes
  useEffect(() => {
    if (selectedFile) {
      setIsLoading(true);
      const fileName = selectedFile.name.replace(/\.[^/.]+$/, "").toUpperCase();
      setName(fileName); // Set name to filename without extension

      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = e.target?.result;
          if (data) {
            // Đọc workbook từ ArrayBuffer
            const workbook = XLSX.read(data, { type: "array" });
            const sheetName = workbook.SheetNames[0];
            const worksheet = workbook.Sheets[sheetName];

            // Chuyển đổi sang JSON
            const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });

            if (jsonData.length > 0) {
              const headers = jsonData[0] as string[];

              // Lọc các dòng trống (một dòng được coi là trống nếu tất cả các ô đều undefined, null, hoặc chuỗi rỗng)
              const filteredRows = (jsonData.slice(1) as any[][]).filter(
                (row) => {
                  return row.some((cell) => {
                    const cellValue =
                      cell !== undefined ? String(cell).trim() : "";
                    return cellValue !== "";
                  });
                }
              );

              // Lưu trữ toàn bộ dữ liệu đã lọc
              setAllRows(filteredRows);

              // Hiển thị số lượng dòng ban đầu
              const initialRows = filteredRows.slice(0, rowsPerPage);
              setVisibleRows(initialRows);

              setExcelData({
                headers,
                rows: initialRows,
              });

              const headerDesc = headers.join(": ...\n") + ": ...";
              setDescription(
                `"${fileName}" dùng để ...\nMô tả các trường:\n${headerDesc}`
              );
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

  // Hàm để tải thêm dữ liệu
  const loadMore = () => {
    if (allRows.length > visibleRows.length) {
      setIsLoadingMore(true);

      // Tính toán số dòng tiếp theo cần tải
      const nextBatch = allRows.slice(
        visibleRows.length,
        visibleRows.length + rowsPerPage
      );

      // Cập nhật dữ liệu hiển thị
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

  // Hàm xử lý sự kiện khi scroll đến cuối bảng
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;

    // Nếu đã scroll đến gần cuối (còn cách 20px) và không đang tải dữ liệu
    if (
      scrollHeight - scrollTop - clientHeight < 20 &&
      !isLoadingMore &&
      allRows.length > visibleRows.length
    ) {
      loadMore();
    }
  };

  // Xử lý việc lưu bảng tính
  const handleSubmit = async () => {
    if (!selectedFile) {
      toast.error("Không tìm thấy file Excel");
      return;
    }

    // Kiểm tra dữ liệu đầu vào
    if (!name.trim()) {
      toast.error("Vui lòng nhập tên bảng tính");
      return;
    }

    setIsSubmitting(true);
    try {
      // Gọi API để upload file
      await sheetService.uploadSheet(name, description, status, selectedFile);

      toast.success("Lưu bảng tính thành công");

      // Đóng modal và gọi callback nếu có
      onOpenChange(false);
      if (onSuccess) onSuccess();
    } catch (error: any) {
      toast.error(
        error?.response?.data?.message || "Có lỗi xảy ra khi lưu bảng tính"
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
            Thêm bảng tính
          </DialogTitle>
        </DialogHeader>
        <div
          className="space-y-6 py-4 overflow-y-auto pr-1"
          onScroll={handleScroll}
        >
          <div className="space-y-2">
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

          <div className="space-y-2">
            <label className="text-sm font-medium">Tên:</label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Tên bảng tính"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">
              Mô tả: <span className="text-red-500">*</span>
            </label>
            <Textarea
              className="min-h-[200px]"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Mô tả về nội dung bảng tính"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Dữ liệu</label>
            <div className="border rounded-md overflow-hidden">
              {isLoading ? (
                <div className="p-4 text-center">
                  Đang đọc dữ liệu từ file Excel...
                </div>
              ) : excelData ? (
                <div className="flex flex-col">
                  <div className="relative max-h-[300px]">
                    <div
                      className="overflow-y-auto overflow-x-auto"
                      style={{ maxHeight: "300px", width: "100%" }}
                      onScroll={handleScroll}
                    >
                      <div style={{ minWidth: "100%", width: "max-content" }}>
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
                                  style={{ minWidth: "150px" }}
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
                    </div>
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
            {isSubmitting ? "Đang lưu..." : "Lưu"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
