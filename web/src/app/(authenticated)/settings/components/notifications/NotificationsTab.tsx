"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
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
import { Badge } from "@/components/ui/badge";
import {
  Plus,
  Pencil,
  Trash2,
  ChevronLeft,
  ChevronRight,
  Filter,
  AlertTriangle,
  Download,
  Edit,
  FilePlus,
  FileDown,
  FileUp,
} from "lucide-react";
import { toast } from "sonner";
import { notificationService } from "@/services/api/notification.service";
import { Notification } from "@/types";
import { MultiStepAddNotificationModal } from "./MultiStepAddNotificationModal";
import { MultiStepEditNotificationModal } from "./MultiStepEditNotificationModal";
import { ExcelImportModal } from "./ExcelImportModal";
import { downloadFile } from "@/lib/file-utils";
import { PaginationSetting } from "../PaginationSetting";
import { StatusFilter } from "../StatusFilter";
import { NotificationTable } from "./NotificationTable";
const ITEMS_PER_PAGE = 10;

export function NotificationsTab() {
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [editingNotification, setEditingNotification] =
    useState<Notification | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);

  // State variables for pagination and data management
  const [selectedNotificationIds, setSelectedNotificationIds] = useState<
    Set<string>
  >(new Set());
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<string>("all");
  const [totalItems, setTotalItems] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [selectedNotificationId, setSelectedNotificationId] = useState<
    string | null
  >(null);

  // Fetch notifications with pagination
  const fetchNotifications = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await notificationService.getPaginationNotification(
        currentPage,
        ITEMS_PER_PAGE,
        status
      );
      setNotifications(response.data);
      setTotalPages(response.total_pages);
      setTotalItems(response.total);
    } catch (error) {
      toast.error("Không thể tải danh sách thông báo.");
    } finally {
      setIsLoading(false);
    }
  }, [currentPage, status]);

  // Fetch data when page or status changes
  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  // Check if all notifications on current page are selected
  const allCurrentPageSelected =
    notifications.length > 0 &&
    notifications.every((notification) =>
      selectedNotificationIds.has(notification.id)
    );

  // Handle select all on current page
  const handleSelectAllOnPage = (checked: boolean) => {
    const newSelected = new Set(selectedNotificationIds);

    if (checked) {
      // Add all items from current page
      notifications.forEach((notification) => {
        newSelected.add(notification.id);
      });
    } else {
      // Remove all items from current page
      notifications.forEach((notification) => {
        newSelected.delete(notification.id);
      });
    }

    setSelectedNotificationIds(newSelected);
  };

  // Handle individual selection
  const handleSelectNotification = (
    notificationId: string,
    checked: boolean
  ) => {
    const newSelected = new Set(selectedNotificationIds);

    if (checked) {
      newSelected.add(notificationId);
    } else {
      newSelected.delete(notificationId);
    }

    setSelectedNotificationIds(newSelected);
  };

  // Handle Excel download
  const handleDownloadExcel = async () => {
    setIsDownloading(true);
    try {
      const blob = await notificationService.downloadNotifications();
      downloadFile(blob, `Cài đặt thông báo.xlsx`);
      toast.success("Đã tải xuống file Excel thành công");
    } catch (error) {
      console.error("Download error:", error);
      toast.error("Không thể tải xuống file Excel");
    } finally {
      setIsDownloading(false);
    }
  };

  // Handle edit notification
  const handleEdit = async (notification: Notification) => {
    try {
      const detailedNotification =
        await notificationService.getNotificationById(notification.id);
      setEditingNotification(detailedNotification);
      setShowEditModal(true);
    } catch (error) {
      toast.error("Không thể tải thông tin thông báo");
    }
  };

  // Open delete confirmation dialog
  const openDeleteConfirmation = () => {
    if (selectedNotificationIds.size > 0) {
      setShowDeleteConfirmation(true);
    } else {
      toast.error("Vui lòng chọn ít nhất một thông báo để xóa");
    }
  };

  const openDeleteConfirmationForSingle = (notificationId: string) => {
    setSelectedNotificationId(notificationId);
    setShowDeleteConfirmation(true);
  };

  // Handle delete selected notifications
  const handleDeleteSelected = async () => {
    if (selectedNotificationIds.size !== 0) {
      setIsDeleting(true);
      try {
        const count = selectedNotificationIds.size;
        const notificationIdsArray = Array.from(selectedNotificationIds);

        // Delete multiple notifications
        await notificationService.deleteNotifications(notificationIdsArray);

        // Clear selected IDs
        setSelectedNotificationIds(new Set());
        toast.success(`Đã xóa ${count} thông báo`);

        // Refresh the list
        fetchNotifications();
      } catch (error) {
        toast.error("Không thể xóa các thông báo đã chọn.");
      } finally {
        setIsDeleting(false);
        setShowDeleteConfirmation(false);
      }
    } else if (selectedNotificationId !== null) {
      setIsDeleting(true);
      try {
        // Delete single notification
        await notificationService.deleteNotification(selectedNotificationId);

        toast.success("Đã xóa thông báo");
        setSelectedNotificationId(null);

        // Refresh the list
        fetchNotifications();
      } catch (error) {
        toast.error("Không thể xóa thông báo.");
      } finally {
        setIsDeleting(false);
        setShowDeleteConfirmation(false);
      }
    }
  };

  // Pagination handlers
  const handlePageChange = (pageNumber: number) => {
    if (pageNumber < 1 || pageNumber > totalPages) return;
    setCurrentPage(pageNumber);
    // Selected IDs cleared when changing page
    setSelectedNotificationIds(new Set());
  };

  // Handle status filter change
  const handleStatusChange = (newStatus: string) => {
    setStatus(newStatus);
    setCurrentPage(1); // Reset to first page when filter changes
    setSelectedNotificationIds(new Set()); // Clear selections when filter changes
  };

  // Get selected notification count
  const selectedCount = selectedNotificationIds.size;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">THÔNG BÁO</h1>
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
              onClick={() => {
                setEditingNotification(null);
                setShowAddModal(true);
              }}
            >
              <Plus className="h-4 w-4" />
              <span>Thêm thông báo mới</span>
            </Button>

            <div className="flex items-center space-x-2 ml-2">
              <Button
                variant="outline"
                className="space-x-2 border-blue-200 text-blue-600"
                onClick={handleDownloadExcel}
                disabled={isDownloading}
              >
                <FileDown className="h-4 w-4" />
                <span>{isDownloading ? "Đang tải..." : "Xuất Excel"}</span>
              </Button>

              <Button
                variant="outline"
                className="space-x-2 border-green-200 text-green-600"
                onClick={() => setShowImportModal(true)}
              >
                <FileUp className="h-4 w-4" />
                <span>Nhập Excel</span>
              </Button>
            </div>
          </div>
        </div>

        <StatusFilter status={status} handleStatusChange={handleStatusChange} />
      </div>
      <NotificationTable
        ITEMS_PER_PAGE={ITEMS_PER_PAGE}
        notifications={notifications}
        status={status}
        selectedNotificationIds={selectedNotificationIds}
        handleSelectAllOnPage={handleSelectAllOnPage}
        allCurrentPageSelected={allCurrentPageSelected}
        handleSelectNotification={handleSelectNotification}
        isLoading={isLoading}
        handleEdit={handleEdit}
        openDeleteConfirmationForSingle={openDeleteConfirmationForSingle}
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
              {selectedNotificationId
                ? "Bạn có chắc chắn muốn xóa thông báo này không? Hành động này không thể hoàn tác."
                : `Bạn có chắc chắn muốn xóa ${selectedNotificationIds.size} thông báo đã chọn không? Hành động này không thể hoàn tác.`}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:justify-end">
            <DialogClose asChild>
              <Button variant="outline" disabled={isDeleting}>
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
              {isDeleting ? "Đang xóa..." : "Xác nhận xóa"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Add Notification Modal */}
      <MultiStepAddNotificationModal
        open={showAddModal}
        onOpenChange={setShowAddModal}
        onSuccess={fetchNotifications}
      />
      {/* Multi-step Edit Notification Modal */}
      <MultiStepEditNotificationModal
        open={showEditModal}
        onOpenChange={setShowEditModal}
        notification={editingNotification}
        onSuccess={fetchNotifications}
      />

      {/* Excel Import Modal */}
      <ExcelImportModal
        open={showImportModal}
        onOpenChange={setShowImportModal}
        onSuccess={fetchNotifications}
      />
    </div>
  );
}
