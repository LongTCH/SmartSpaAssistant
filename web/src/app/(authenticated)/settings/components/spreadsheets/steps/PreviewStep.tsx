"use client";

import { ExcelData } from "@/types";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useEffect, useRef } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ColumnConfig } from "@/types";
import * as XLSX from "xlsx";
import { formatDate } from "@/lib/helpers";

// Helper constants & functions
const validColumnTypeLabels: Record<string, string> = {
  String: "Văn bản ngắn",
  Text: "Văn bản dài",
  Integer: "Số nguyên",
  Numeric: "Số thập phân",
  DateTime: "Ngày giờ",
  Boolean: "True/False",
};

// Màu tương ứng cho từng kiểu dữ liệu
const typeColors: Record<string, string> = {
  String: "bg-blue-100 text-blue-800 hover:bg-blue-100",
  Text: "bg-purple-100 text-purple-800 hover:bg-purple-100",
  Integer: "bg-green-100 text-green-800 hover:bg-green-100",
  Numeric: "bg-emerald-100 text-emerald-800 hover:bg-emerald-100",
  DateTime: "bg-amber-100 text-amber-800 hover:bg-amber-100",
  Boolean: "bg-pink-100 text-pink-800 hover:bg-pink-100",
};

// Định dạng dữ liệu Excel cho hiển thị - tương tự như trong PreviewSheetModal
const formatExcelValue = (value: any, type: string): string => {
  // Trả về chuỗi rỗng nếu giá trị rỗng
  if (value === null || value === undefined || value === "") {
    return "";
  }

  // Xử lý các kiểu dữ liệu cụ thể
  switch (type) {
    case "DateTime":
      // Xử lý trường hợp giá trị đã là datetime từ cơ sở dữ liệu (ISO string)
      if (
        typeof value === "string" &&
        /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(value)
      ) {
        try {
          const date = new Date(value);
          if (!isNaN(date.getTime())) {
            return formatDate ? formatDate(date) : date.toLocaleString();
          }
        } catch (e) {
          // Nếu không parse được thì trả về chuỗi gốc
        }
      }

      // Xử lý giá trị số có thể là ngày giờ từ Excel (DATE + TIME)
      if (typeof value === "number") {
        // Excel lưu giá trị ngày thường nằm trong khoảng từ 1 đến ~50000
        if (value >= 1 && value < 50000) {
          try {
            // Thử chuyển đổi sang Date sử dụng thư viện XLSX
            const excelDate = XLSX.SSF.parse_date_code(value);

            // Nếu đây là giá trị ngày hợp lệ
            if (excelDate && excelDate.y >= 1900 && excelDate.y <= 2100) {
              const jsDate = new Date(
                excelDate.y,
                excelDate.m - 1,
                excelDate.d
              );

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

              return formatDate ? formatDate(jsDate) : jsDate.toLocaleString();
            }
          } catch (e) {
            // Nếu không phải ngày giờ hợp lệ, xử lý như số bình thường
          }
        }
      }

      // Date object
      if (value instanceof Date) {
        return formatDate ? formatDate(value) : value.toLocaleString();
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
                return formatDate ? formatDate(date) : date.toLocaleString();
              }
            } catch (e) {
              // Nếu không chuyển đổi được, giữ nguyên chuỗi
            }
          }
        }
      }
      // Trả về chuỗi gốc nếu không xác định được định dạng ngày tháng
      return String(value);

    case "Boolean":
      return value ? "✓" : "✗";

    case "Integer":
    case "Numeric":
      // Đảm bảo hiển thị dạng số
      return !isNaN(Number(value)) ? String(Number(value)) : String(value);

    default:
      return String(value);
  }
};

interface PreviewStepProps {
  excelData: ExcelData | null;
  columnConfigs: ColumnConfig[];
  visibleRows: any[][];
  allRows: any[][];
  isLoadingMore: boolean;
  handleScroll: (e: React.UIEvent<HTMLDivElement>) => void;
  loadMoreRows: () => void;
}

export function PreviewStep({
  excelData,
  columnConfigs,
  visibleRows,
  allRows,
  isLoadingMore,
  handleScroll,
  loadMoreRows,
}: PreviewStepProps) {
  // Reference to the scroll container
  const scrollRef = useRef<HTMLDivElement>(null);

  // Adjust the visible rows to exclude the header
  const limitedVisibleRows = allRows.slice(1, 11); // Skip the header row and show only the first 10 data rows

  // Observer for handling "infinite scroll"
  useEffect(() => {
    if (!scrollRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        if (
          entry.isIntersecting &&
          !isLoadingMore &&
          allRows.length > limitedVisibleRows.length
        ) {
          loadMoreRows();
        }
      },
      { threshold: 0.1 }
    );

    observer.observe(scrollRef.current);

    return () => {
      if (scrollRef.current) {
        observer.unobserve(scrollRef.current);
      }
    };
  }, [limitedVisibleRows, allRows, isLoadingMore, loadMoreRows]);

  if (!excelData || !columnConfigs.length) {
    return (
      <div className="p-4 text-center text-muted-foreground">
        Không có dữ liệu để xem trước. Vui lòng tải lên file Excel.
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Container chính */}
      <div className="flex-1 max-h-[500px]">
        <div className="relative">
          <div
            className="overflow-y-auto overflow-x-auto"
            style={{ maxHeight: "500px", width: "100%" }}
            onScroll={handleScroll}
          >
            <div style={{ minWidth: "100%", width: "max-content" }}>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-16 border-r sticky top-0 left-0 bg-slate-100 z-20">
                      STT
                    </TableHead>
                    {columnConfigs.map((col, i) => (
                      <TableHead
                        key={i}
                        className="font-medium py-3 sticky top-0 bg-slate-100 z-10 border-r"
                        style={{ minWidth: "200px" }}
                      >
                        <div className="flex flex-col gap-2">
                          <div className="flex items-center gap-2">
                            <span>{col.column_name}</span>
                            {col.is_index && (
                              <Badge
                                variant="outline"
                                className="bg-blue-50 border-blue-300 text-blue-700 hover:bg-blue-50"
                              >
                                Index
                              </Badge>
                            )}
                          </div>
                          <div>
                            <Badge
                              variant="secondary"
                              className={
                                typeColors[col.column_type] || "bg-gray-100"
                              }
                            >
                              {validColumnTypeLabels[col.column_type] ||
                                col.column_type}
                            </Badge>
                          </div>
                        </div>
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {limitedVisibleRows.map((row, rowIndex) => (
                    <TableRow key={rowIndex}>
                      <TableCell className="text-muted-foreground font-medium sticky left-0 bg-white z-10 border-r">
                        {rowIndex + 1}
                      </TableCell>
                      {columnConfigs.map((col, colIndex) => (
                        <TableCell
                          key={colIndex}
                          className={
                            colIndex < columnConfigs.length - 1
                              ? "border-r"
                              : ""
                          }
                          style={{ minWidth: "200px" }}
                        >
                          {row[colIndex] !== undefined
                            ? formatExcelValue(row[colIndex], col.column_type)
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
          <div className="py-4 px-2">
            <div className="flex space-x-4">
              <Skeleton className="h-4 w-[100px]" />
              <Skeleton className="h-4 w-[200px]" />
              <Skeleton className="h-4 w-[150px]" />
            </div>
          </div>
        )}

        {/* Loading trigger element */}
        <div ref={scrollRef} style={{ height: "10px" }}></div>
      </div>

      {/* Phần footer cố định */}
      <div className="flex justify-between items-center py-2 bg-white mt-2">
        <div className="text-xs text-gray-500">
          Hiển thị 10 dòng trong tổng số {allRows.length - 1} dòng
        </div>

        <div className="text-xs text-gray-500">
          <span>Cuộn ngang để xem thêm cột &rarr;</span>
        </div>
      </div>
    </div>
  );
}
