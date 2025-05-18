"use client";

import { useState, useMemo, useEffect, useRef, useCallback } from "react";
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
  Upload,
  Plus,
  Pencil,
  Trash2,
  ChevronLeft,
  ChevronRight,
  Filter,
  AlertTriangle,
  FileDown,
  FileUp,
} from "lucide-react";
import { AddScriptModal } from "./AddScriptModal";
import { EditScriptModal } from "./EditScriptModal";
import { UploadScriptModal } from "./UploadScriptModal";
import { Script } from "@/types";
import { toast } from "sonner";
import { scriptService } from "@/services/api/script.service";
import { PaginationSetting } from "../PaginationSetting";
import { ScriptTable } from "./ScriptTable";
import { StatusFilter } from "../StatusFilter";
// Constants
const ITEMS_PER_PAGE = 10;
let oldPage = 1;
let oldStatus = "all";

export function ScriptsTab() {
  // State
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [editScriptId, setEditScriptId] = useState<string | null>(null);
  const [selectedScriptIds, setSelectedScriptIds] = useState<Set<string>>(
    new Set()
  );
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [scripts, setScripts] = useState<Script[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<string>("all");
  const [totalItems, setTotalItems] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);
  const [selectedScriptId, setSelectedScriptId] = useState<string | null>(null); // State for file upload modal
  const [showUploadModal, setShowUploadModal] = useState(false);

  // Sử dụng useRef để theo dõi trạng thái đã tải
  const hasInitialFetch = useRef(false);

  // Fetch scripts data from API
  const fetchScripts = useCallback(async () => {
    // Nếu đang tải, không fetch thêm
    if (isLoading) return;
    setIsLoading(true);
    try {
      const response = await scriptService.getPaginationScript(
        currentPage,
        ITEMS_PER_PAGE,
        status
      );

      setScripts(response.data);
      setTotalPages(response.total_pages);
      setTotalItems(response.total);
    } catch {
      toast.error("Không thể tải danh sách kịch bản.");
    } finally {
      setIsLoading(false);
    }
  }, [currentPage, status, isLoading]);

  // Fetch data when page or status changes
  useEffect(() => {
    if (
      !hasInitialFetch.current ||
      oldPage !== currentPage ||
      oldStatus !== status
    ) {
      fetchScripts();
      hasInitialFetch.current = true;
      // Update old values after fetch
      oldPage = currentPage;
      oldStatus = status;
    }
  }, [currentPage, status, fetchScripts]);

  // Check if all scripts on current page are selected
  const allCurrentPageSelected = useMemo(() => {
    if (scripts.length === 0) return false;
    return scripts.every((script) => selectedScriptIds.has(script.id));
  }, [scripts, selectedScriptIds]);

  // Handle select all on current page
  const handleSelectAllOnPage = (checked: boolean) => {
    const newSelected = new Set(selectedScriptIds);

    if (checked) {
      // Add all items from current page
      scripts.forEach((script) => {
        newSelected.add(script.id);
      });
    } else {
      // Remove all items from current page
      scripts.forEach((script) => {
        newSelected.delete(script.id);
      });
    }

    setSelectedScriptIds(newSelected);
  };

  // Handle individual selection
  const handleSelectScript = (scriptId: string, checked: boolean) => {
    const newSelected = new Set(selectedScriptIds);

    if (checked) {
      newSelected.add(scriptId);
    } else {
      newSelected.delete(scriptId);
    }

    setSelectedScriptIds(newSelected);
  };

  // Open delete confirmation dialog
  const openDeleteConfirmation = () => {
    if (selectedScriptIds.size > 0) {
      setShowDeleteConfirmation(true);
    } else {
      toast.error("Vui lòng chọn ít nhất một kịch bản để xóa");
    }
  };

  const openDeleteConfirmationForSingle = () => {
    setShowDeleteConfirmation(true);
  };

  // Handle single script delete (when clicking trash icon)
  const handleSingleScriptDelete = (scriptId: string) => {
    setSelectedScriptId(scriptId);
  };
  useEffect(() => {
    if (selectedScriptId) {
      openDeleteConfirmationForSingle();
    }
  }, [selectedScriptId]);

  // Handle delete selected scripts (after confirmation)
  const handleDeleteSelected = async () => {
    if (selectedScriptIds.size !== 0) {
      setIsDeleting(true);
      try {
        const count = selectedScriptIds.size;
        const scriptIdsArray = Array.from(selectedScriptIds);

        // Use the deleteScripts API to delete multiple scripts at once
        await scriptService.deleteScripts(scriptIdsArray);

        // Clear selected IDs
        setSelectedScriptIds(new Set());

        // Refetch scripts to update the list
        await fetchScripts();

        toast.success(`Đã xóa ${count} kịch bản`);
        setShowDeleteConfirmation(false);
      } catch {
        toast.error("Có lỗi xảy ra khi xóa kịch bản");
      } finally {
        setIsDeleting(false);
      }
    } else if (selectedScriptId !== null) {
      setIsDeleting(true);
      try {
        // Use the deleteScript API to delete a single script
        await scriptService.deleteScript(selectedScriptId);

        // Clear selected ID
        setSelectedScriptId(null);

        // Refetch scripts to update the list
        await fetchScripts();

        toast.success("Đã xóa kịch bản");
        setShowDeleteConfirmation(false);
      } catch {
        toast.error("Có lỗi xảy ra khi xóa kịch bản");
      } finally {
        setIsDeleting(false);
      }
    }
  };

  // Pagination handlers
  const handlePageChange = (pageNumber: number) => {
    if (pageNumber < 1 || pageNumber > totalPages) return;
    setCurrentPage((prev) => {
      oldPage = prev;
      return pageNumber;
    });
    // Selected IDs cleared when changing page
    setSelectedScriptIds(new Set());
  };

  // Handle status filter change
  const handleStatusChange = (newStatus: string) => {
    setStatus((prev) => {
      oldStatus = prev;
      return newStatus;
    });
    setCurrentPage((prev) => {
      oldPage = prev;
      return 1;
    }); // Reset to first page when filter changes
    setSelectedScriptIds(new Set()); // Clear selections when filter changes
  };

  // Handle edit script
  const handleEditScript = (scriptId: string) => {
    setEditScriptId(scriptId);
    setShowEditModal(true);
  };

  // Handle download scripts
  const handleDownloadScripts = async () => {
    const loadingToast = toast.loading("Đang tải xuống kịch bản...");
    try {
      // Get the file blob using our service
      const blob = await scriptService.downloadScripts();

      // Use the downloadFile utility
      await downloadFile(blob, "Kịch bản.xlsx");

      // Dismiss loading toast and show success
      toast.dismiss(loadingToast);
      toast.success("Tải xuống kịch bản thành công");
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error("Không thể tải xuống kịch bản");
      console.error("Download error:", error);
    }
  };

  // Handle modal close
  const handleUploadModalClose = (open: boolean) => {
    setShowUploadModal(open);
  };

  // Handle refetch after successful edit or add
  const handleScriptUpdated = () => {
    fetchScripts();
  };

  // Get selected script count
  const selectedCount = selectedScriptIds.size;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">KỊCH BẢN</h1>
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
          <div className="flex items-center space-x-2">
            <Button
              className="bg-[#6366F1] hover:bg-[#4F46E5] text-white space-x-2"
              onClick={() => setShowAddModal(true)}
            >
              <Plus className="h-4 w-4" />
              <span>Thêm kịch bản mới</span>
            </Button>

            <div className="flex items-center space-x-2 ml-2">
              <Button
                variant="outline"
                className="space-x-2 border-blue-200 text-blue-600"
                onClick={handleDownloadScripts}
              >
                <FileDown className="h-4 w-4" />
                <span>Xuất Excel</span>
              </Button>
              <Button
                variant="outline"
                className="space-x-2 border-green-200 text-green-600"
                onClick={() => setShowUploadModal(true)}
              >
                <FileUp className="h-4 w-4" />
                <span>Nhập Excel</span>
              </Button>
            </div>
          </div>
        </div>

        <StatusFilter status={status} handleStatusChange={handleStatusChange} />
      </div>
      <ScriptTable
        ITEMS_PER_PAGE={ITEMS_PER_PAGE}
        scripts={scripts}
        isLoading={isLoading}
        status={status}
        selectedScriptIds={selectedScriptIds}
        allCurrentPageSelected={allCurrentPageSelected}
        handleSelectScript={handleSelectScript}
        handleSelectAllOnPage={handleSelectAllOnPage}
        handleSingleScriptDelete={handleSingleScriptDelete}
        handleEditScript={handleEditScript}
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
              {selectedCount !== 0 ? selectedCount : 1} kịch bản đã chọn? Hành
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
      {/* Modals */}
      <AddScriptModal
        open={showAddModal}
        onOpenChange={setShowAddModal}
        onSuccess={handleScriptUpdated}
      />
      <EditScriptModal
        open={showEditModal}
        onOpenChange={setShowEditModal}
        scriptId={editScriptId}
        onSuccess={handleScriptUpdated}
      />
      {/* File Upload Modal */}
      <UploadScriptModal
        open={showUploadModal}
        onOpenChange={handleUploadModalClose}
        onSuccess={handleScriptUpdated}
      />
    </div>
  );
}
