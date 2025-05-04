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
import { toast } from "sonner";
import { Sheet, SheetRow } from "@/types";
import { sheetService } from "@/services/api/sheet.service";

interface EditSpreadsheetModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  sheet: Sheet | null;
  onSuccess?: () => void;
}

export function EditSpreadsheetModal({
  open,
  onOpenChange,
  sheet,
  onSuccess,
}: EditSpreadsheetModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [sheetData, setSheetData] = useState<Partial<Sheet>>({
    name: "",
    description: "",
    status: "published",
    schema: [],
  });

  // Data display state
  const [currentPage, setCurrentPage] = useState(0);
  const [rows, setRows] = useState<SheetRow[]>([]);
  const [hasMore, setHasMore] = useState(true);
  const [isLoadingRows, setIsLoadingRows] = useState(false);
  const [totalRows, setTotalRows] = useState(0);
  const rowsPerPage = 20;

  // Fetch sheet data when sheetId changes
  useEffect(() => {
    const fetchSheetData = async () => {
      if (!sheet || !open) return;

      setIsLoading(true);

      try {
        setSheetData(sheet);

        // Start loading first page of rows
        loadRows(0);
      } catch (error) {
        toast.error("Không thể tải thông tin bảng tính");
      } finally {
        setIsLoading(false);
      }
    };

    fetchSheetData();
  }, [sheet, open]);

  // Function to handle loading rows
  const loadRows = async (skip: number = rows.length) => {
    if (!sheet) return;

    setIsLoadingRows(true);
    try {
      const response = await sheetService.getPagingSheetRows(
        sheet.id,
        skip,
        rowsPerPage
      );

      if (skip === 0) {
        // First page
        setRows(response.data);
      } else {
        // Append to existing rows
        setRows((prev) => [...prev, ...response.data]);
      }

      setTotalRows(response.total);
      setHasMore(response.has_next);
      setCurrentPage(Math.floor(skip / rowsPerPage));
    } catch (error) {
      toast.error("Không thể tải dữ liệu bảng tính");
    } finally {
      setIsLoadingRows(false);
    }
  };

  // Load more rows when scrolling
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;

    // If scrolled near bottom and more data exists
    if (
      scrollHeight - scrollTop - clientHeight < 20 &&
      !isLoadingRows &&
      hasMore
    ) {
      const nextSkip = rows.length;
      loadRows(nextSkip);
    }
  };

  // Handle load more button click
  const handleLoadMore = () => {
    if (!isLoadingRows && hasMore) {
      const nextSkip = rows.length;
      loadRows(nextSkip);
    }
  };

  const handleChange = (field: keyof Sheet, value: any) => {
    setSheetData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);

    try {
      // Validate required fields
      if (!sheetData.name) {
        toast.error("Vui lòng điền tên bảng tính");
        setIsSubmitting(false);
        return;
      }

      if (!sheet) {
        toast.error("ID bảng tính không hợp lệ");
        setIsSubmitting(false);
        return;
      }

      // Call API to update sheet
      await sheetService.updateSheet(
        sheet.id,
        sheetData.name!,
        sheetData.description || "",
        sheetData.status || "published"
      );

      toast.success("Đã cập nhật bảng tính thành công");
      onSuccess?.();
      onOpenChange(false);
    } catch (error: any) {
      toast.error(
        error?.response?.data?.message || "Có lỗi xảy ra khi cập nhật bảng tính"
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
            Chỉnh sửa bảng tính
          </DialogTitle>
        </DialogHeader>

        {isLoading ? (
          <div className="py-8 space-y-4">
            <div className="h-8 bg-gray-200 animate-pulse rounded w-1/3 mx-auto"></div>
            <div className="h-24 bg-gray-200 animate-pulse rounded"></div>
            <div className="h-24 bg-gray-200 animate-pulse rounded"></div>
          </div>
        ) : (
          <div
            className="space-y-6 py-4 overflow-y-auto pr-1"
            onScroll={handleScroll}
          >
            <div className="flex flex-col md:flex-row gap-4 items-start">
              <div className="space-y-2 flex-1">
                <label className="text-sm font-medium">
                  Tên: <span className="text-red-500">*</span>
                </label>
                <Input
                  placeholder="Tên bảng tính"
                  value={sheetData.name}
                  onChange={(e) => handleChange("name", e.target.value)}
                />
              </div>

              <div className="space-y-2 md:w-[200px]">
                <label className="text-sm font-medium">Trạng thái:</label>
                <Select
                  value={sheetData.status}
                  onValueChange={(value: "published" | "draft") =>
                    handleChange("status", value)
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Xuất bản" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="published">Xuất bản</SelectItem>
                    <SelectItem value="draft">Bản nháp</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">
                Mô tả: <span className="text-red-500">*</span>
              </label>
              <Textarea
                className="min-h-[200px]"
                placeholder="Mô tả về nội dung và cách sử dụng bảng tính"
                value={sheetData.description}
                onChange={(e) => handleChange("description", e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Dữ liệu</label>
              <div className="border rounded-md overflow-hidden">
                {isLoadingRows && rows.length === 0 ? (
                  <div className="p-4 text-center">Đang tải dữ liệu...</div>
                ) : rows.length > 0 && sheetData.schema ? (
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
                                {sheetData.schema.map((header, index) => (
                                  <TableHead
                                    key={index}
                                    className={`${
                                      index < sheetData.schema!.length - 1
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
                              {rows.map((row, rowIndex) => (
                                <TableRow key={rowIndex}>
                                  <TableCell className="border-r">
                                    {rowIndex + 1}
                                  </TableCell>
                                  {sheetData.schema!.map(
                                    (header, cellIndex) => (
                                      <TableCell
                                        key={cellIndex}
                                        className={
                                          cellIndex <
                                          sheetData.schema!.length - 1
                                            ? "border-r"
                                            : ""
                                        }
                                      >
                                        {row[header] !== undefined
                                          ? String(row[header])
                                          : ""}
                                      </TableCell>
                                    )
                                  )}
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </div>
                      </div>
                    </div>

                    {isLoadingRows && (
                      <div className="p-2 text-center text-sm text-muted-foreground">
                        Đang tải thêm dữ liệu...
                      </div>
                    )}

                    {!isLoadingRows && hasMore && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="mx-auto my-2"
                        onClick={handleLoadMore}
                      >
                        Tải thêm dữ liệu
                      </Button>
                    )}

                    <div className="p-2 text-center text-sm text-muted-foreground">
                      Đang hiển thị {rows.length} / {totalRows} dòng
                    </div>
                  </div>
                ) : (
                  <div className="p-4 text-center">
                    Không có dữ liệu để hiển thị
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        <DialogFooter className="flex-shrink-0">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isLoading || isSubmitting}
          >
            Hủy
          </Button>
          <Button
            className="bg-[#6366F1] hover:bg-[#4F46E5] text-white"
            onClick={handleSubmit}
            disabled={isLoading || isSubmitting}
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
                Đang cập nhật...
              </span>
            ) : (
              "Cập nhật"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
