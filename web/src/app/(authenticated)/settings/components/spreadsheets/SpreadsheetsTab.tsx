"use client";

import { useState, useRef, useEffect, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Download,
  Plus,
  Pencil,
  Trash2,
  ChevronLeft,
  ChevronRight,
  Filter,
  AlertTriangle,
} from "lucide-react";
import { AddSpreadsheetModal } from "./AddSpreadsheetModal";
import { EditSpreadsheetModal } from "./EditSpreadsheetModal";
import { toast } from "sonner";
import { Sheet } from "@/types";
import { sheetService } from "@/services/api/sheet.service";

// Constants
const ITEMS_PER_PAGE = 5;

export function SpreadsheetsTab() {
  const [showSpreadsheetModal, setShowSpreadsheetModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // New state variables
  const [selectedSheetIds, setSelectedSheetIds] = useState<Set<string>>(
    new Set()
  );
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [sheets, setSheets] = useState<Sheet[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<string>("all");
  const [totalItems, setTotalItems] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [selectedSheetId, setSelectedSheetId] = useState<string | null>(null);
  const [showEditSpreadsheetModal, setShowEditSpreadsheetModal] =
    useState(false);
  const [editingSheet, setEditingSheet] = useState<Sheet | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    // Check if the file is Excel
    const validExcelTypes = [
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", // .xlsx
      "application/vnd.ms-excel", // .xls
    ];

    if (!validExcelTypes.includes(file.type)) {
      toast.error("Chỉ chấp nhận file Excel (.xlsx, .xls)");
      event.target.value = "";
      return;
    }

    setSelectedFile(file);
    setShowSpreadsheetModal(true);
  };

  const handleAddSpreadsheetClick = () => {
    // Trigger file input click
    fileInputRef.current?.click();
  };

  // Handle modal close
  const handleModalClose = (open: boolean) => {
    setShowSpreadsheetModal(open);
    if (!open) {
      // Reset selected file on close
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  // Sử dụng useRef để theo dõi trạng thái đã tải
  const hasInitialFetch = useRef(false);

  const fetchSheets = async () => {
    try {
      // Nếu đang tải, không fetch thêm
      if (isLoading) return;
      setIsLoading(true);

      const response = await sheetService.getPaginationSheet(
        currentPage,
        ITEMS_PER_PAGE,
        status
      );

      setSheets(response.data);
      setTotalPages(response.total_pages);
      setTotalItems(response.total);
    } catch (error) {
      toast.error("Không thể tải danh sách bảng tính");
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch data when page or status changes
  useEffect(() => {
    // Chỉ fetch khi thay đổi status hoặc page, hoặc chưa tải lần đầu
    if (!hasInitialFetch.current || currentPage > 1 || status !== "all") {
      fetchSheets();
      hasInitialFetch.current = true;
    }
  }, [currentPage, status]);

  // Check if all sheets on current page are selected
  const allCurrentPageSelected = useMemo(() => {
    if (sheets.length === 0) return false;
    return sheets.every((sheet) => selectedSheetIds.has(sheet.id));
  }, [sheets, selectedSheetIds]);

  // Handle select all on current page
  const handleSelectAllOnPage = (checked: boolean) => {
    const newSelected = new Set(selectedSheetIds);

    if (checked) {
      // Add all items from current page
      sheets.forEach((sheet) => {
        newSelected.add(sheet.id);
      });
    } else {
      // Remove all items from current page
      sheets.forEach((sheet) => {
        newSelected.delete(sheet.id);
      });
    }

    setSelectedSheetIds(newSelected);
  };

  // Handle individual selection
  const handleSelectSheet = (sheetId: string, checked: boolean) => {
    const newSelected = new Set(selectedSheetIds);

    if (checked) {
      newSelected.add(sheetId);
    } else {
      newSelected.delete(sheetId);
    }

    setSelectedSheetIds(newSelected);
  };

  // Open delete confirmation dialog
  const openDeleteConfirmation = () => {
    if (selectedSheetIds.size > 0) {
      setShowDeleteConfirmation(true);
    } else {
      toast.error("Vui lòng chọn ít nhất một bảng tính để xóa");
    }
  };

  const openDeleteConfirmationForSingle = () => {
    setShowDeleteConfirmation(true);
  };

  // Handle single sheet delete (when clicking trash icon)
  const handleSingleSheetDelete = (sheetId: string) => {
    setSelectedSheetId(sheetId);
    openDeleteConfirmationForSingle();
  };

  // Handle delete selected sheets (after confirmation)
  const handleDeleteSelected = async () => {
    if (selectedSheetIds.size !== 0) {
      setIsDeleting(true);
      try {
        const count = selectedSheetIds.size;
        const sheetIdsArray = Array.from(selectedSheetIds);

        // Use the deleteSheets API to delete multiple sheets at once
        await sheetService.deleteSheets(sheetIdsArray);

        // Clear selected IDs
        setSelectedSheetIds(new Set());

        // Refetch sheets to update the list
        await fetchSheets();

        toast.success(`Đã xóa ${count} bảng tính`);
        setShowDeleteConfirmation(false);
      } catch (error) {
        toast.error("Có lỗi xảy ra khi xóa bảng tính");
      } finally {
        setIsDeleting(false);
      }
    } else if (selectedSheetId !== null) {
      setIsDeleting(true);
      try {
        // Use the deleteSheet API to delete a single sheet
        await sheetService.deleteSheet(selectedSheetId);

        // Clear selected ID
        setSelectedSheetId(null);

        // Refetch sheets to update the list
        await fetchSheets();

        toast.success("Đã xóa bảng tính");
        setShowDeleteConfirmation(false);
      } catch (error) {
        toast.error("Có lỗi xảy ra khi xóa bảng tính");
      } finally {
        setIsDeleting(false);
      }
    }
  };

  // Pagination handlers
  const handlePageChange = (pageNumber: number) => {
    if (pageNumber < 1 || pageNumber > totalPages) return;
    setCurrentPage(pageNumber);
    // Selected IDs cleared when changing page
    setSelectedSheetIds(new Set());
  };

  // Handle status filter change
  const handleStatusChange = (newStatus: string) => {
    setStatus(newStatus);
    setCurrentPage(1); // Reset to first page when filter changes
    setSelectedSheetIds(new Set()); // Clear selections when filter changes
  };

  // Handle sheet download
  const handleDownloadSheet = async (sheetId: string, sheetName: string) => {
    const loadingToast = toast.loading("Đang tải bảng tính...");
    try {
      // Show loading toast

      // Get the file blob using our service
      const blob = await sheetService.downloadSheet(sheetId);

      // Create a URL for the blob
      const url = URL.createObjectURL(blob);

      // Create a temporary anchor element to trigger download
      const link = document.createElement("a");
      link.href = url;
      link.download = `${sheetName}.xlsx`;
      document.body.appendChild(link);
      link.click();

      // Clean up
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      // Dismiss loading toast and show success
      toast.dismiss(loadingToast);
      toast.success("Tải bảng tính thành công");
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error("Không thể tải bảng tính");
    }
  };

  // Handle sheet edit
  const handleEditSheet = (sheet: Sheet) => {
    setEditingSheet(sheet);
    setShowEditSpreadsheetModal(true);
  };

  // Get selected sheet count
  const selectedCount = selectedSheetIds.size;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">BẢNG TÍNH</h1>

      {/* Hidden file input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept=".xlsx,.xls"
        className="hidden"
      />

      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            className="border-dashed relative"
            onClick={openDeleteConfirmation}
            disabled={selectedCount === 0}
          >
            <div
              className={`absolute -top-2 -right-2 w-5 h-5 rounded-full ${
                selectedCount > 0 ? "bg-red-500" : "bg-gray-300"
              } text-white flex items-center justify-center text-xs`}
            >
              {selectedCount}
            </div>
            <Trash2
              className={`h-5 w-5 ${
                selectedCount > 0 ? "text-red-500" : "text-gray-500"
              }`}
            />
          </Button>
          <Button
            className="bg-[#6366F1] hover:bg-[#4F46E5] text-white space-x-2"
            onClick={handleAddSpreadsheetClick}
          >
            <Plus className="h-4 w-4" />
            <span>Thêm bảng tính mới</span>
          </Button>
        </div>

        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4 text-gray-500" />
          <Select value={status} onValueChange={handleStatusChange}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Lọc theo trạng thái" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tất cả</SelectItem>
              <SelectItem value="published">Xuất bản</SelectItem>
              <SelectItem value="draft">Bản nháp</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="border rounded-md">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-12 border-r">
                <Checkbox
                  checked={allCurrentPageSelected}
                  onCheckedChange={handleSelectAllOnPage}
                  disabled={sheets.length === 0}
                />
              </TableHead>
              <TableHead className="text-[#6366F1] border-r w-2xl">
                Tên bảng tính
              </TableHead>
              <TableHead className="text-[#6366F1] border-r w-24">
                Trạng thái
              </TableHead>
              <TableHead className="text-right text-[#6366F1]">
                Thao tác
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              // Loading state
              Array(ITEMS_PER_PAGE)
                .fill(0)
                .map((_, index) => (
                  <TableRow key={`loading-${index}`}>
                    <TableCell className="border-r">
                      <div className="w-4 h-4 bg-gray-200 animate-pulse rounded"></div>
                    </TableCell>
                    <TableCell className="border-r">
                      <div className="w-full h-4 bg-gray-200 animate-pulse rounded"></div>
                    </TableCell>
                    <TableCell className="border-r">
                      <div className="w-24 h-4 bg-gray-200 animate-pulse rounded"></div>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end space-x-2">
                        <div className="w-8 h-8 bg-gray-200 animate-pulse rounded"></div>
                        <div className="w-8 h-8 bg-gray-200 animate-pulse rounded"></div>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
            ) : sheets.length > 0 ? (
              sheets.map((sheet) => (
                <TableRow key={sheet.id}>
                  <TableCell className="border-r">
                    <Checkbox
                      checked={selectedSheetIds.has(sheet.id)}
                      onCheckedChange={(checked) =>
                        handleSelectSheet(sheet.id, checked === true)
                      }
                    />
                  </TableCell>
                  <TableCell className="border-r">{sheet.name}</TableCell>
                  <TableCell className="border-r">
                    <div
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        sheet.status === "published"
                          ? "bg-green-100 text-green-800"
                          : "bg-yellow-100 text-yellow-800"
                      }`}
                    >
                      {sheet.status === "published" ? "Xuất bản" : "Bản nháp"}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end space-x-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        title="Tải về"
                        onClick={() =>
                          handleDownloadSheet(sheet.id, sheet.name)
                        }
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        title="Chỉnh sửa"
                        onClick={() => handleEditSheet(sheet)}
                      >
                        <Pencil className="h-4 w-4 text-blue-500" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        title="Xóa"
                        onClick={() => handleSingleSheetDelete(sheet.id)}
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={4}
                  className="text-center py-8 text-gray-500"
                >
                  Không có bảng tính nào{" "}
                  {status !== "all" &&
                    `có trạng thái "${
                      status === "published" ? "Xuất bản" : "Bản nháp"
                    }"`}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {totalPages > 0 && (
        <div className="flex justify-between items-center mt-6">
          <div className="text-sm text-gray-500">
            {totalItems > 0
              ? `Hiển thị ${
                  (currentPage - 1) * ITEMS_PER_PAGE + 1
                } - ${Math.min(
                  currentPage * ITEMS_PER_PAGE,
                  totalItems
                )} trong số ${totalItems} bảng tính`
              : "Không có bảng tính nào"}
          </div>

          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="icon"
              className="h-10 w-10"
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>

            {/* Generate page buttons */}
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              // Show at most 5 page buttons
              let pageNum;
              if (totalPages <= 5) {
                // If 5 or fewer pages, show all
                pageNum = i + 1;
              } else if (currentPage <= 3) {
                // If near the start, show 1,2,3,4,5
                pageNum = i + 1;
              } else if (currentPage >= totalPages - 2) {
                // If near the end, show last 5 pages
                pageNum = totalPages - 4 + i;
              } else {
                // Otherwise, show current page and 2 on each side
                pageNum = currentPage - 2 + i;
              }

              return (
                <Button
                  key={pageNum}
                  variant={pageNum === currentPage ? "default" : "outline"}
                  className={
                    pageNum === currentPage
                      ? "bg-[#6366F1] text-white h-10 w-10"
                      : "h-10 w-10"
                  }
                  onClick={() => handlePageChange(pageNum)}
                >
                  {pageNum}
                </Button>
              );
            })}

            <Button
              variant="outline"
              size="icon"
              className="h-10 w-10"
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <Dialog
        open={showDeleteConfirmation}
        onOpenChange={setShowDeleteConfirmation}
      >
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-xl">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              Xác nhận xóa
            </DialogTitle>
            <DialogDescription>
              Bạn có chắc chắn muốn xóa{" "}
              {selectedCount !== 0 ? selectedCount : 1} bảng tính đã chọn? Hành
              động này không thể hoàn tác.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:justify-end">
            <DialogClose asChild>
              <Button type="button" variant="outline" disabled={isDeleting}>
                Hủy
              </Button>
            </DialogClose>
            <Button
              type="button"
              variant="destructive"
              className="bg-red-500 hover:bg-red-600 text-white"
              onClick={handleDeleteSelected}
              disabled={isDeleting}
            >
              {isDeleting ? (
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
                  Đang xóa...
                </span>
              ) : (
                "Xóa"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Spreadsheet Modal */}
      <EditSpreadsheetModal
        open={showEditSpreadsheetModal}
        onOpenChange={setShowEditSpreadsheetModal}
        sheet={editingSheet}
        onSuccess={fetchSheets}
      />

      <AddSpreadsheetModal
        open={showSpreadsheetModal}
        onOpenChange={handleModalClose}
        selectedFile={selectedFile}
        onSuccess={fetchSheets}
      />
    </div>
  );
}
