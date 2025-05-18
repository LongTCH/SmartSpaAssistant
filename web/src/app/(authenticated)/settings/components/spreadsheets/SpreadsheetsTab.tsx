"use client";

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { downloadFile } from "@/lib/file-utils";
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
  Eye,
} from "lucide-react";
import { MultiStepAddSpreadsheetModal } from "./MultiStepAddSpreadsheetModal";
import { MultiStepEditSpreadsheetModal } from "./MultiStepEditSpreadsheetModal";
import { PreviewSheetModal } from "./PreviewSheetModal";
import { toast } from "sonner";
import { Sheet } from "@/types";
import { sheetService } from "@/services/api/sheet.service";
import { PaginationSetting } from "../PaginationSetting";
import { StatusFilter } from "../StatusFilter";
import { SpreadSheetTable } from "./SpreadSheetTable";
// Constants
const ITEMS_PER_PAGE = 10;

export function SpreadsheetsTab() {
  const [showSpreadsheetModal, setShowSpreadsheetModal] = useState(false);

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

  // State cho modal xem trước bảng tính
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [previewingSheet, setPreviewingSheet] = useState<Sheet | null>(null);

  const handleAddSpreadsheetClick = () => {
    // Directly open the multi-step modal
    setShowSpreadsheetModal(true);
  };

  // Handle modal close
  const handleModalClose = (open: boolean) => {
    setShowSpreadsheetModal(open);
  };

  const fetchSheets = useCallback(async () => {
    // REMOVED: if (isLoading) return;
    // This check is problematic: if isLoading is not a dependency, it uses a stale value.
    // If isLoading IS a dependency, it causes the infinite loop.
    setIsLoading(true);
    try {
      const response = await sheetService.getPaginationSheet(
        currentPage,
        ITEMS_PER_PAGE,
        status
      );
      setSheets(response.data);
      setTotalPages(response.total_pages);
      setTotalItems(response.total);
    } catch {
      // console.error("Error fetching sheets:", error);
      toast.error("Không thể tải danh sách trang tính.");
    } finally {
      setIsLoading(false);
    }
  }, [
    currentPage,
    status,
    // REMOVED: isLoading, // This was the primary cause of the infinite loop
    setIsLoading, // Stable setter, can be included
    setSheets, // Stable setter, can be included
    setTotalPages, // Stable setter, can be included
    setTotalItems, // Stable setter, can be included
  ]);

  // Fetch data when page or status changes
  useEffect(() => {
    fetchSheets();
  }, [fetchSheets]);

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
      } catch {
        // console.error("Error deleting sheet:", error);
        toast.error("Không thể xóa trang tính.");
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
      } catch {
        // console.error("Error deleting sheet:", error);
        toast.error("Không thể xóa trang tính.");
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
      // Get the file blob using our service
      const blob = await sheetService.downloadSheet(sheetId);

      // Use the downloadFile utility
      await downloadFile(blob, `${sheetName}.xlsx`);

      // Dismiss loading toast and show success
      toast.dismiss(loadingToast);
      toast.success("Tải bảng tính thành công");
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error("Không thể tải bảng tính");
      console.error("Error downloading sheet:", error);
    }
  };

  // Handle sheet edit
  const handleEditSheet = (sheet: Sheet) => {
    setEditingSheet(sheet);
    setShowEditSpreadsheetModal(true);
  };

  // Handle sheet preview
  const handlePreviewSheet = (sheet: Sheet) => {
    setPreviewingSheet(sheet);
    setShowPreviewModal(true);
  };

  // Get selected sheet count
  const selectedCount = selectedSheetIds.size;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">BẢNG TÍNH</h1>

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

        <StatusFilter status={status} handleStatusChange={handleStatusChange} />
      </div>

      <SpreadSheetTable
        ITEMS_PER_PAGE={ITEMS_PER_PAGE}
        sheets={sheets}
        isLoading={isLoading}
        status={status}
        selectedSheetIds={selectedSheetIds}
        allCurrentPageSelected={allCurrentPageSelected}
        handleSelectSheet={handleSelectSheet}
        handleSelectAllOnPage={handleSelectAllOnPage}
        handlePreviewSheet={handlePreviewSheet}
        handleDownloadSheet={handleDownloadSheet}
        handleEditSheet={handleEditSheet}
        handleSingleSheetDelete={handleSingleSheetDelete}
      />
      {/* Pagination */}
      <PaginationSetting
        totalItems={totalItems}
        currentPage={currentPage}
        ITEMS_PER_PAGE={ITEMS_PER_PAGE}
        totalPages={totalPages}
        handlePageChange={handlePageChange}
      />

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

      {/* Multi-step Add Spreadsheet Modal */}
      <MultiStepAddSpreadsheetModal
        open={showSpreadsheetModal}
        onOpenChange={handleModalClose}
        onSuccess={fetchSheets}
      />

      {/* Multi-step Edit Spreadsheet Modal */}
      <MultiStepEditSpreadsheetModal
        open={showEditSpreadsheetModal}
        onOpenChange={setShowEditSpreadsheetModal}
        sheet={editingSheet}
        onSuccess={fetchSheets}
      />

      {/* Preview Sheet Modal */}
      <PreviewSheetModal
        open={showPreviewModal}
        onOpenChange={setShowPreviewModal}
        sheet={previewingSheet}
      />
    </div>
  );
}
