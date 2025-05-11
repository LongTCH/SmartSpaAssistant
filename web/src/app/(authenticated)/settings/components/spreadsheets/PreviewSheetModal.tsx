"use client";

import { useState, useEffect, useCallback } from "react";
import * as XLSX from "xlsx";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogClose,
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
import { Sheet } from "@/types";
import { sheetService } from "@/services/api/sheet.service";
import { toast } from "sonner";
import { formatDate } from "@/lib/helpers";

// Định dạng dữ liệu Excel cho hiển thị
const formatExcelValue = (value: any): any => {
  // Trả về chuỗi rỗng nếu giá trị rỗng
  if (value === null || value === undefined || value === "") {
    return "";
  }

  // Xử lý trường hợp giá trị đã là datetime từ cơ sở dữ liệu (ISO string)
  if (
    typeof value === "string" &&
    /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(value)
  ) {
    try {
      const date = new Date(value);
      if (!isNaN(date.getTime())) {
        return formatDate(date);
      }
    } catch {
      // Nếu không parse được thì trả về chuỗi gốc
      return value;
    }
  }

  // Xử lý giá trị số có thể là ngày giờ từ Excel
  if (typeof value === "number") {
    // Excel lưu giá trị ngày thường nằm trong khoảng từ 1 đến ~50000
    if (value >= 1 && value < 50000) {
      try {
        // Thử chuyển đổi sang Date
        const excelDate = XLSX.SSF.parse_date_code(value);

        // Nếu đây là giá trị ngày hợp lệ
        if (excelDate && excelDate.y >= 1900 && excelDate.y <= 2100) {
          const jsDate = new Date(excelDate.y, excelDate.m - 1, excelDate.d);

          // Kiểm tra xem có phần thời gian không
          const hasTime = Math.abs(value - Math.floor(value)) > 0;

          // Nếu có cả ngày và giờ (từ DATE+TIME)
          if (hasTime) {
            // Tính phần thời gian (số thập phân biểu thị phần nhỏ của 24h)
            const timeValue = value - Math.floor(value);
            const totalMinutes = Math.round(timeValue * 24 * 60);
            const hours = Math.floor(totalMinutes / 60);
            const minutes = totalMinutes % 60;

            // Thêm thời gian vào đối tượng Date
            jsDate.setHours(hours, minutes, 0);
          }

          return formatDate(jsDate);
        }
      } catch {
        // Nếu không phải ngày giờ hợp lệ, xử lý như số bình thường
        return value;
      }
    }
  }

  // Date object
  if (value instanceof Date) {
    return formatDate(value);
  }

  // Xử lý các định dạng chuỗi ngày tháng phổ biến
  if (typeof value === "string") {
    const datePatterns = [
      // Mẫu dd/MM/yyyy hoặc d/M/yyyy
      /^(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})$/,
      // Mẫu yyyy-MM-dd hoặc yyyy/MM/dd
      /^(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})$/,
    ];

    for (const pattern of datePatterns) {
      if (pattern.test(value)) {
        try {
          // Chuyển đổi sang Date (cẩn thận với các định dạng khác nhau)
          const date = new Date(value);
          if (!isNaN(date.getTime())) {
            return formatDate(date);
          }
        } catch {
          // Nếu không chuyển đổi được, giữ nguyên chuỗi
        }
      }
    }
  }

  return value;
};

interface PreviewSheetModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  sheet: Sheet | null;
}

export function PreviewSheetModal({
  open,
  onOpenChange,
  sheet,
}: PreviewSheetModalProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [rows, setRows] = useState<any[]>([]);
  const [page, setPage] = useState(1);
  const [totalRows, setTotalRows] = useState(0);
  const rowsPerPage = 10;

  const fetchSheetData = useCallback(async () => {
    if (!sheet?.id) return;

    setIsLoading(true);
    try {
      const skip = (page - 1) * rowsPerPage;
      const response = await sheetService.getPagingSheetRows(
        sheet.id,
        skip,
        rowsPerPage
      );

      // API trả về cấu trúc phân trang: { data, total, skip, limit, has_next, has_prev }
      if (response && response.data) {
        setRows(response.data);
        setTotalRows(response.total || 0);
      } else {
        setRows([]);
        setTotalRows(0);
      }
    } catch {
      toast.error("Không thể tải dữ liệu bảng tính");
      setRows([]);
      setTotalRows(0);
    } finally {
      setIsLoading(false);
    }
  }, [sheet?.id, page, setIsLoading, setRows, setTotalRows]);

  useEffect(() => {
    if (open && sheet) {
      fetchSheetData();
    } else {
      // Reset state when modal closes
      setRows([]);
      setPage(1);
      setTotalRows(0);
    }
  }, [open, sheet, page, fetchSheetData]);

  const loadNextPage = () => {
    setPage((prev) => prev + 1);
  };

  const loadPrevPage = () => {
    setPage((prev) => Math.max(prev - 1, 1));
  };

  // Get column headers from column_config
  const getColumnHeaders = (): string[] => {
    // Sử dụng column_config từ đối tượng sheet
    if (sheet?.column_config && Array.isArray(sheet.column_config)) {
      try {
        // Trích xuất tên cột từ column_config
        return sheet.column_config.map((col) => col.column_name);
      } catch {}
    } else if (rows.length > 0 && typeof rows[0] === "object") {
      // Backup: lấy tên cột từ dữ liệu nếu không có column_config
      return Object.keys(rows[0]).filter(
        (key) => !(key.toLowerCase() === "id" || key.toLowerCase() === "_id")
      );
    }

    return []; // Không có dữ liệu
  };

  // Lấy kiểu dữ liệu cho mỗi cột (để định dạng đúng)
  const getColumnType = (columnName: string): string => {
    if (sheet?.column_config && Array.isArray(sheet.column_config)) {
      const column = sheet.column_config.find(
        (col) => col.column_name === columnName
      );
      return column?.column_type || "String";
    }
    return "String";
  };

  // Định dạng giá trị cell dựa vào column_config
  const formatCellValueByConfig = (value: any, columnName: string): string => {
    const columnType = getColumnType(columnName);

    // Xử lý các kiểu dữ liệu cụ thể theo column_config
    if (columnType === "DateTime") {
      return formatExcelValue(value);
    } else if (columnType === "Integer" || columnType === "Numeric") {
      return value !== null && value !== undefined ? String(value) : "";
    } else {
      return value !== null && value !== undefined ? String(value) : "";
    }
  };

  const columnHeaders = getColumnHeaders();
  const hasNextPage = page * rowsPerPage < totalRows;
  const hasPrevPage = page > 1;
  const startRow = (page - 1) * rowsPerPage + 1;
  const endRow = Math.min(page * rowsPerPage, totalRows);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[90vw] max-h-screen overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold">
            Xem trước dữ liệu - {sheet?.name}
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-auto min-h-[400px]">
          {isLoading ? (
            <div className="flex justify-center items-center h-full">
              <div className="flex flex-col items-center space-y-4">
                <div className="w-12 h-12 border-t-4 border-blue-500 border-solid rounded-full animate-spin"></div>
                <p className="text-lg font-medium">Đang tải dữ liệu...</p>
              </div>
            </div>
          ) : rows.length > 0 ? (
            <div className="flex flex-col">
              <div className="relative max-h-[85vh]">
                <div
                  className="overflow-y-auto overflow-x-auto"
                  style={{ maxHeight: "85vh", width: "100%" }}
                >
                  <div style={{ minWidth: "100%", width: "max-content" }}>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          {columnHeaders.map(
                            (header: string, index: number) => (
                              <TableHead
                                key={index}
                                className={`${
                                  index < columnHeaders.length - 1
                                    ? "border-r"
                                    : ""
                                } sticky top-0 bg-background z-10`}
                                style={{ minWidth: "150px" }}
                              >
                                {header}
                              </TableHead>
                            )
                          )}
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {rows.map((row, rowIndex) => {
                          return (
                            <TableRow key={rowIndex}>
                              {columnHeaders.map(
                                (header: string, index: number) => {
                                  // Đảm bảo hiển thị dữ liệu đúng cách ngay cả khi cấu trúc dữ liệu thay đổi
                                  const cellValue =
                                    typeof row === "object" && row !== null
                                      ? row[header] !== undefined
                                        ? formatCellValueByConfig(
                                            row[header],
                                            header
                                          )
                                        : ""
                                      : "";

                                  return (
                                    <TableCell
                                      key={index}
                                      className={
                                        index < columnHeaders.length - 1
                                          ? "border-r"
                                          : ""
                                      }
                                    >
                                      {cellValue}
                                    </TableCell>
                                  );
                                }
                              )}
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex justify-center items-center h-full">
              <p className="text-muted-foreground">Không có dữ liệu</p>
            </div>
          )}
        </div>

        <div className="flex justify-between items-center pt-4">
          <div className="text-sm text-gray-500">
            {totalRows > 0
              ? `Hiển thị ${startRow} - ${endRow} trong số ${totalRows} dòng dữ liệu`
              : "Không có dữ liệu"}
          </div>

          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={loadPrevPage}
              disabled={!hasPrevPage}
            >
              Trang trước
            </Button>
            <span className="text-sm">Trang {page}</span>
            <Button
              variant="outline"
              size="sm"
              onClick={loadNextPage}
              disabled={!hasNextPage}
            >
              Trang sau
            </Button>
          </div>
        </div>

        <DialogFooter>
          <DialogClose asChild>
            <Button type="button">Đóng</Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
