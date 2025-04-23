"use client";

import { useState, useMemo, useEffect, useRef } from "react";
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
import { AddKeywordModal } from "./AddKeywordModal";
import { EditKeywordModal } from "./EditKeywordModal";
import { UploadKeywordModal } from "./UploadKeywordModal";
import { Interest } from "@/types";
import { toast } from "sonner";
import { interestService } from "@/services/api/interest.service";

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
  // File upload
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Sử dụng useRef để theo dõi trạng thái đã tải
  const hasInitialFetch = useRef(false);

  // Fetch interests data from API
  const fetchInterests = async () => {
    // Nếu đang tải, không fetch thêm
    if (isLoading) return;
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
    } catch (error) {
      toast.error("Không thể tải danh sách từ khóa");
    } finally {
      setIsLoading(false);
    }
  };

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
    }
  }, [currentPage, status]);

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
      toast.error("Vui lòng chọn ít nhất một từ khóa để xóa");
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

        toast.success(`Đã xóa ${count} từ khóa`);
        setShowDeleteConfirmation(false);
      } catch (error) {
        toast.error("Có lỗi xảy ra khi xóa từ khóa");
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

        toast.success("Đã xóa từ khóa");
        setShowDeleteConfirmation(false);
      } catch (error) {
        toast.error("Có lỗi xảy ra khi xóa từ khóa");
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
    const loadingToast = toast.loading("Đang tải xuống từ khóa...");
    try {
      // Get the file blob using our service
      const blob = await interestService.downloadInterests();

      // Create a URL for the blob
      const url = URL.createObjectURL(blob);

      // Create a temporary anchor element to trigger download
      const link = document.createElement("a");
      link.href = url;
      link.download = "Xu hướng Khách hàng.xlsx";
      document.body.appendChild(link);
      link.click();

      // Clean up
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      // Dismiss loading toast and show success
      toast.dismiss(loadingToast);
      toast.success("Tải xuống từ khóa thành công");
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error("Không thể tải xuống từ khóa");
    }
  };

  // Handle file upload button click
  const handleUploadButtonClick = () => {
    fileInputRef.current?.click();
  };

  // Handle file selection
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
    setShowUploadModal(true);
  };

  // Handle modal close
  const handleUploadModalClose = (open: boolean) => {
    setShowUploadModal(open);
    if (!open) {
      // Reset selected file on close
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  // Handle refetch after successful edit or add
  const handleInterestUpdated = () => {
    fetchInterests();
  };

  // Get selected interest count
  const selectedCount = selectedInterestIds.size;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">TỪ KHÓA</h1>

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
            variant="outline"
            className="space-x-2"
            onClick={handleDownloadInterests}
          >
            <Download className="h-4 w-4" />
            <span>Export file</span>
          </Button>
          <Button
            variant="outline"
            className="space-x-2"
            onClick={handleUploadButtonClick}
          >
            <Upload className="h-4 w-4" />
            <span>Upload file</span>
          </Button>
          <Button
            className="bg-[#6366F1] hover:bg-[#4F46E5] text-white space-x-2"
            onClick={() => setShowAddModal(true)}
          >
            <Plus className="h-4 w-4" />
            <span>Thêm từ khóa mới</span>
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
                  disabled={interests.length === 0}
                />
              </TableHead>
              <TableHead className="text-[#6366F1] border-r">
                Tên từ khóa
              </TableHead>
              <TableHead className="text-[#6366F1] border-r">
                Từ khoá liên quan
              </TableHead>
              <TableHead className="text-[#6366F1] border-r w-24">
                Trạng thái
              </TableHead>
              <TableHead className="text-right text-[#6366F1] w-36">
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
            ) : interests.length > 0 ? (
              interests.map((interest) => (
                <TableRow key={interest.id}>
                  <TableCell className="border-r">
                    <Checkbox
                      checked={selectedInterestIds.has(interest.id)}
                      onCheckedChange={(checked) =>
                        handleSelectInterest(interest.id, checked === true)
                      }
                    />
                  </TableCell>
                  <TableCell className="border-r">{interest.name}</TableCell>
                  <TableCell className="border-r">
                    {interest.related_terms}
                  </TableCell>
                  <TableCell className="border-r">
                    <div
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        interest.status === "published"
                          ? "bg-green-100 text-green-800"
                          : "bg-yellow-100 text-yellow-800"
                      }`}
                    >
                      {interest.status === "published"
                        ? "Xuất bản"
                        : "Bản nháp"}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end space-x-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        title="Chỉnh sửa"
                        onClick={() => handleEditInterest(interest.id)}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        title="Xóa"
                        onClick={() => handleSingleInterestDelete(interest.id)}
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
                  colSpan={5}
                  className="text-center py-8 text-gray-500"
                >
                  Không có từ khóa nào{" "}
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
                )} trong số ${totalItems} từ khóa`
              : "Không có từ khóa nào"}
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
              {selectedCount !== 0 ? selectedCount : 1} từ khóa đã chọn? Hành
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
      <AddKeywordModal
        open={showAddModal}
        onOpenChange={setShowAddModal}
        onSuccess={handleInterestUpdated}
      />

      <EditKeywordModal
        open={showEditModal}
        onOpenChange={setShowEditModal}
        interestId={editInterestId}
        onSuccess={handleInterestUpdated}
      />

      {/* File Upload Modal */}
      <UploadKeywordModal
        open={showUploadModal}
        onOpenChange={handleUploadModalClose}
        selectedFile={selectedFile}
        onSuccess={handleInterestUpdated}
      />
    </div>
  );
}
