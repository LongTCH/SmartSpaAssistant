"use client";

import { useState, useMemo, useEffect, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { downloadFile } from "@/lib/file-utils";

import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import { Plus, Trash2, AlertTriangle, FileDown, FileUp } from "lucide-react";
import { AddInterestModal } from "./AddInterestModal";
import { EditInterestModal } from "./EditInterestModal";
import { UploadInterestModal } from "./UploadInterestModal";
import { Interest } from "@/types";
import { toast } from "sonner";
import { interestService } from "@/services/api/interest.service";
import { PaginationSetting } from "../PaginationSetting";
import { InterestTable } from "./InterestTable";
import { StatusFilter } from "../StatusFilter";
// Constants
const ITEMS_PER_PAGE = 10;
let oldPage = 1;
let oldStatus = "all";

export function InterestsTab() {
  // State
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [editInterestId, setEditInterestId] = useState<string | null>(null);
  const [selectedInterestIds, setSelectedInterestIds] = useState<Set<string>>(
    new Set()
  );
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [interests, setInterests] = useState<Interest[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<string>("all");
  const [totalItems, setTotalItems] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);
  const [selectedInterestId, setSelectedInterestId] = useState<string | null>(
    null
  );
  // File upload modal
  const [showUploadModal, setShowUploadModal] = useState(false);
  // Sử dụng useRef để theo dõi trạng thái đã tải
  const hasInitialFetch = useRef(false);
  const loadingRef = useRef(false);

  // Fetch interests data from API
  const fetchInterests = useCallback(async () => {
    // Nếu đang tải, không fetch thêm
    if (loadingRef.current) return;
    loadingRef.current = true;
    setIsLoading(true);
    try {
      const response = await interestService.getPaginationInterest(
        currentPage,
        ITEMS_PER_PAGE,
        status
      );

      setInterests(response.data);
      setTotalPages(response.total_pages);
      setTotalItems(response.total);
    } catch {
      toast.error("Không thể tải danh sách nhãn");
    } finally {
      setIsLoading(false);
      loadingRef.current = false;
    }
  }, [currentPage, status]); // Removed isLoading to prevent infinite loop

  // Fetch data when page or status changes
  useEffect(() => {
    // Chỉ fetch khi thay đổi status hoặc page, hoặc chưa tải lần đầu
    if (
      !hasInitialFetch.current ||
      oldPage !== currentPage ||
      oldStatus !== status
    ) {
      fetchInterests();
      hasInitialFetch.current = true;
      // Update old values after fetch
      oldPage = currentPage;
      oldStatus = status;
    }
  }, [currentPage, status, fetchInterests]);

  // Check if all interests on current page are selected
  const allCurrentPageSelected = useMemo(() => {
    if (interests.length === 0) return false;
    return interests.every((interest) => selectedInterestIds.has(interest.id));
  }, [interests, selectedInterestIds]);

  // Handle select all on current page
  const handleSelectAllOnPage = (checked: boolean) => {
    const newSelected = new Set(selectedInterestIds);

    if (checked) {
      // Add all items from current page
      interests.forEach((interest) => {
        newSelected.add(interest.id);
      });
    } else {
      // Remove all items from current page
      interests.forEach((interest) => {
        newSelected.delete(interest.id);
      });
    }

    setSelectedInterestIds(newSelected);
  };

  // Handle individual selection
  const handleSelectInterest = (interestId: string, checked: boolean) => {
    const newSelected = new Set(selectedInterestIds);

    if (checked) {
      newSelected.add(interestId);
    } else {
      newSelected.delete(interestId);
    }

    setSelectedInterestIds(newSelected);
  };

  // Open delete confirmation dialog
  const openDeleteConfirmation = () => {
    if (selectedInterestIds.size > 0) {
      setShowDeleteConfirmation(true);
    } else {
      toast.error("Vui lòng chọn ít nhất một nhãn để xóa");
    }
  };

  const openDeleteConfirmationForSingle = () => {
    setShowDeleteConfirmation(true);
  };

  // Handle single interest delete (when clicking trash icon)
  const handleSingleInterestDelete = (interestId: string) => {
    setSelectedInterestId(interestId);
  };
  useEffect(() => {
    if (selectedInterestId) {
      openDeleteConfirmationForSingle();
    }
  }, [selectedInterestId]);

  // Handle delete selected interests (after confirmation)
  const handleDeleteSelected = async () => {
    if (selectedInterestIds.size !== 0) {
      setIsDeleting(true);
      try {
        const count = selectedInterestIds.size;
        const interestIdsArray = Array.from(selectedInterestIds);

        // Use the deleteInterests API to delete multiple interests at once
        await interestService.deleteInterests(interestIdsArray);

        // Clear selected IDs
        setSelectedInterestIds(new Set());

        // Refetch interests to update the list
        await fetchInterests();

        toast.success(`Đã xóa ${count} nhãn`);
        setShowDeleteConfirmation(false);
      } catch {
        toast.error("Có lỗi xảy ra khi xóa nhãn");
      } finally {
        setIsDeleting(false);
      }
    } else if (selectedInterestId !== null) {
      setIsDeleting(true);
      try {
        // Use the deleteInterest API to delete a single interest
        await interestService.deleteInterest(selectedInterestId);

        // Clear selected ID
        setSelectedInterestId(null);

        // Refetch interests to update the list
        await fetchInterests();

        toast.success("Đã xóa nhãn");
        setShowDeleteConfirmation(false);
      } catch {
        toast.error("Có lỗi xảy ra khi xóa nhãn");
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
    setSelectedInterestIds(new Set());
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
    setSelectedInterestIds(new Set()); // Clear selections when filter changes
  };

  // Handle edit interest
  const handleEditInterest = (interestId: string) => {
    setEditInterestId(interestId);
    setShowEditModal(true);
  };
  // Handle download interests
  const handleDownloadInterests = async () => {
    const loadingToast = toast.loading("Đang tải xuống nhãn...");
    try {
      // Get the file blob using our service
      const blob = await interestService.downloadInterests();

      // Use the downloadFile utility
      await downloadFile(blob, "Nhãn Khách hàng.xlsx");

      // Dismiss loading toast and show success
      toast.dismiss(loadingToast);
      toast.success("Tải xuống nhãn thành công");
    } catch {
      toast.dismiss(loadingToast);
      toast.error("Không thể tải xuống nhãn");
    }
  };

  // Handle modal close
  const handleUploadModalClose = (open: boolean) => {
    setShowUploadModal(open);
  };

  // Handle refetch after successful edit or add
  const handleInterestUpdated = () => {
    fetchInterests();
  };

  // Get selected interest count
  const selectedCount = selectedInterestIds.size;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">NHÃN</h1>
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
              <span>Thêm nhãn mới</span>
            </Button>

            <div className="flex items-center space-x-2 ml-2">
              <Button
                variant="outline"
                className="space-x-2 border-blue-200 text-blue-600"
                onClick={handleDownloadInterests}
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
      <InterestTable
        ITEMS_PER_PAGE={ITEMS_PER_PAGE}
        interests={interests}
        isLoading={isLoading}
        status={status}
        selectedInterestIds={selectedInterestIds}
        allCurrentPageSelected={allCurrentPageSelected}
        handleSelectInterest={handleSelectInterest}
        handleSelectAllOnPage={handleSelectAllOnPage}
        handleEditInterest={handleEditInterest}
        handleSingleInterestDelete={handleSingleInterestDelete}
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
              {selectedCount !== 0 ? selectedCount : 1} nhãn đã chọn? Hành động
              này không thể hoàn tác.
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
      <AddInterestModal
        open={showAddModal}
        onOpenChange={setShowAddModal}
        onSuccess={handleInterestUpdated}
      />
      <EditInterestModal
        open={showEditModal}
        onOpenChange={setShowEditModal}
        interestId={editInterestId}
        onSuccess={handleInterestUpdated}
      />
      {/* File Upload Modal */}
      <UploadInterestModal
        open={showUploadModal}
        onOpenChange={handleUploadModalClose}
        onSuccess={handleInterestUpdated}
      />
    </div>
  );
}
