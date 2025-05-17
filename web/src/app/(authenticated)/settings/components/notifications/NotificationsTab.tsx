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
} from "lucide-react";
import { toast } from "sonner";
import { MultiStepAddNotificationModal } from "./MultiStepAddNotificationModal";
import { MultiStepEditNotificationModal } from "./MultiStepEditNotificationModal";
import { Notification } from "@/types";
import { notificationService } from "@/services/api/notification.service";

// Constants
const ITEMS_PER_PAGE = 10;

export function NotificationsTab() {
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingNotification, setEditingNotification] =
    useState<Notification | null>(null);

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
        <div style={{ overflowX: "auto", width: "100%" }}>
          <Table className="w-full">
            <TableHeader>
              <TableRow>
                <TableHead
                  className="w-12 border-r"
                  style={{ width: "48px", minWidth: "48px" }}
                >
                  <Checkbox
                    checked={allCurrentPageSelected && notifications.length > 0}
                    onCheckedChange={handleSelectAllOnPage}
                    disabled={notifications.length === 0 || isLoading}
                  />
                </TableHead>
                <TableHead
                  className="text-[#6366F1] border-r"
                  style={{ width: "180px", minWidth: "180px" }}
                >
                  Nhãn thông báo
                </TableHead>
                <TableHead className="text-[#6366F1] border-r">Mô tả</TableHead>
                <TableHead
                  className="text-[#6366F1] border-r"
                  style={{ width: "96px", minWidth: "96px" }}
                >
                  Trạng thái
                </TableHead>
                <TableHead
                  className="text-right text-[#6366F1]"
                  style={{ width: "120px", minWidth: "120px" }}
                >
                  Thao tác
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {
                /*
                 */ isLoading ? (
                  // Loading state
                  Array.from({ length: ITEMS_PER_PAGE }).map((_, index) => (
                    <TableRow key={`loading-${index}`}>
                      {/*
                       */}
                      <TableCell className="border-r">
                        <div className="w-4 h-4 bg-gray-200 animate-pulse rounded"></div>
                      </TableCell>
                      {/*
                       */}
                      <TableCell className="border-r">
                        <div className="w-full h-4 bg-gray-200 animate-pulse rounded"></div>
                      </TableCell>
                      {/*
                       */}
                      <TableCell className="border-r">
                        <div className="w-full h-4 bg-gray-200 animate-pulse rounded"></div>
                      </TableCell>
                      {/*
                       */}
                      <TableCell className="border-r">
                        <div className="w-24 h-4 bg-gray-200 animate-pulse rounded"></div>
                      </TableCell>
                      {/*
                       */}
                      <TableCell className="text-right">
                        <div className="flex justify-end space-x-2">
                          <div className="w-8 h-8 bg-gray-200 animate-pulse rounded"></div>
                          <div className="w-8 h-8 bg-gray-200 animate-pulse rounded"></div>
                          <div className="w-8 h-8 bg-gray-200 animate-pulse rounded"></div>
                        </div>
                      </TableCell>
                      {/*
                       */}
                    </TableRow>
                  ))
                ) : notifications.length === 0 ? (
                  <TableRow>
                    {/*
                     */}
                    <TableCell
                      colSpan={5}
                      className="text-center py-8 text-gray-500"
                    >
                      <div className="w-full text-center">
                        Không có thông báo nào
                        {status !== "all" &&
                          ` có trạng thái "${
                            status === "published" ? "Xuất bản" : "Bản nháp"
                          }"}`}
                      </div>
                    </TableCell>
                    {/*
                     */}
                  </TableRow>
                ) : (
                  notifications.map((notification) => (
                    <TableRow key={notification.id}>
                      {/*
                       */}
                      <TableCell className="border-r">
                        <Checkbox
                          checked={selectedNotificationIds.has(notification.id)}
                          onCheckedChange={(checked) =>
                            handleSelectNotification(notification.id, !!checked)
                          }
                        />
                      </TableCell>
                      {/*
                       */}
                      <TableCell className="border-r">
                        <div className="flex items-center gap-2">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: notification.color }}
                          ></div>
                          <span className="font-medium">
                            {notification.label}
                          </span>
                        </div>
                      </TableCell>
                      {/*
                       */}
                      <TableCell className="border-r max-w-xs">
                        <div
                          className="w-full overflow-hidden text-ellipsis whitespace-nowrap pr-2"
                          title={notification.description}
                        >
                          {notification.description}
                        </div>
                      </TableCell>
                      {/*
                       */}
                      <TableCell className="border-r">
                        <div
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            notification.status === "published"
                              ? "bg-green-100 text-green-800"
                              : "bg-yellow-100 text-yellow-800"
                          }`}
                        >
                          {notification.status === "published"
                            ? "Xuất bản"
                            : "Bản nháp"}
                        </div>
                      </TableCell>
                      {/*
                       */}
                      <TableCell className="text-right">
                        <div className="flex justify-end space-x-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            title="Tải về mẫu thông báo"
                            onClick={() =>
                              toast.info("Chức năng đang phát triển")
                            }
                          >
                            <Download className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            title="Chỉnh sửa"
                            onClick={() => handleEdit(notification)}
                          >
                            <Pencil className="h-4 w-4 text-blue-500" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            title="Xóa"
                            onClick={() =>
                              openDeleteConfirmationForSingle(notification.id)
                            }
                          >
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        </div>
                      </TableCell>
                      {/*
                       */}
                    </TableRow>
                  ))
                )
              }
              {/*
               */}
            </TableBody>
          </Table>
        </div>
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
                )} trong số ${totalItems} thông báo`
              : "Không có thông báo nào"}
          </div>{" "}
          <div className="flex items-center space-x-2">
            {/* Nút First Page */}
            <Button
              variant="outline"
              size="icon"
              className="h-10 w-10"
              onClick={() => handlePageChange(1)}
              disabled={currentPage === 1}
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              <ChevronLeft className="h-4 w-4 -ml-3" />
            </Button>

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

            {/* Nút Last Page */}
            <Button
              variant="outline"
              size="icon"
              className="h-10 w-10"
              onClick={() => handlePageChange(totalPages)}
              disabled={currentPage === totalPages}
            >
              <ChevronRight className="h-4 w-4 mr-1" />
              <ChevronRight className="h-4 w-4 -ml-3" />
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
        </DialogContent>{" "}
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
    </div>
  );
}
