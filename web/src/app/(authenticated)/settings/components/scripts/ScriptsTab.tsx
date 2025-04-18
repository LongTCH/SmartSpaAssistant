"use client";

import { useState, useMemo, useEffect } from "react";
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
  Upload,
  Plus,
  Pencil,
  Trash2,
  ChevronLeft,
  ChevronRight,
  Filter,
  AlertTriangle,
} from "lucide-react";
import { AddScriptModal } from "./AddScriptModal";
import { EditScriptModal } from "./EditScriptModal";
import { Script } from "@/types";
import { toast } from "sonner";
import { scriptService } from "@/services/api/script.service";

// Constants
const ITEMS_PER_PAGE = 5;

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
  const [isLoading, setIsLoading] = useState(true);
  const [status, setStatus] = useState<string>("all");
  const [totalItems, setTotalItems] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);
  const [selectedScriptId, setSelectedScriptId] = useState<string | null>(null);

  // Fetch scripts data from API
  const fetchScripts = async () => {
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
    } catch (error) {
      toast.error("Không thể tải danh sách kịch bản");
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch data when page or status changes
  useEffect(() => {
    fetchScripts();
  }, [currentPage, status]);

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
      } catch (error) {
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
      } catch (error) {
        toast.error("Có lỗi xảy ra khi xóa kịch bản");
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
    setSelectedScriptIds(new Set());
  };

  // Handle status filter change
  const handleStatusChange = (newStatus: string) => {
    setStatus(newStatus);
    setCurrentPage(1); // Reset to first page when filter changes
    setSelectedScriptIds(new Set()); // Clear selections when filter changes
  };

  // Handle edit script
  const handleEditScript = (scriptId: string) => {
    setEditScriptId(scriptId);
    setShowEditModal(true);
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
          <Button variant="outline" className="space-x-2">
            <Download className="h-4 w-4" />
            <span>Export file</span>
          </Button>
          <Button variant="outline" className="space-x-2">
            <Upload className="h-4 w-4" />
            <span>Upload file</span>
          </Button>
          <Button
            className="bg-[#6366F1] hover:bg-[#4F46E5] text-white space-x-2"
            onClick={() => setShowAddModal(true)}
          >
            <Plus className="h-4 w-4" />
            <span>Thêm kịch bản mới</span>
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
                  disabled={scripts.length === 0}
                />
              </TableHead>
              <TableHead className="text-[#6366F1] border-r">
                Tên kịch bản
              </TableHead>
              <TableHead className="text-[#6366F1] border-r">
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
            ) : scripts.length > 0 ? (
              scripts.map((script) => (
                <TableRow key={script.id}>
                  <TableCell className="border-r">
                    <Checkbox
                      checked={selectedScriptIds.has(script.id)}
                      onCheckedChange={(checked) =>
                        handleSelectScript(script.id, checked === true)
                      }
                    />
                  </TableCell>
                  <TableCell className="border-r">{script.name}</TableCell>
                  <TableCell className="border-r">
                    <div
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        script.status === "published"
                          ? "bg-green-100 text-green-800"
                          : "bg-yellow-100 text-yellow-800"
                      }`}
                    >
                      {script.status === "published" ? "Xuất bản" : "Bản nháp"}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end space-x-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        title="Chỉnh sửa"
                        onClick={() => handleEditScript(script.id)}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        title="Xóa"
                        onClick={() => handleSingleScriptDelete(script.id)}
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
                  Không có kịch bản nào{" "}
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
                )} trong số ${totalItems} kịch bản`
              : "Không có kịch bản nào"}
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
    </div>
  );
}
