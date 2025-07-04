"use client";

import { useState, useEffect, Suspense, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Download, Search, Trash2, AlertTriangle } from "lucide-react";
import { Input } from "@/components/ui/input";
import { KeywordFilter } from "./components/KeywordFilter";
import { CustomerTable } from "./components/CustomerTable";
import { CustomerPagination } from "./components/CustomerPagination";
import { LoadingScreen } from "@/components/loading-screen";
import { GuestInfoModal } from "../../../components/guest-info/GuestInfoModal";
import { guestService } from "@/services/api/guest.service";
import { interestService } from "@/services/api/interest.service";
import { Conversation, Interest } from "@/types";
import { toast } from "sonner";

export default function CustomerManagement() {
  const [selectedKeywords, setSelectedKeywords] = useState<string[]>([]);
  const [pendingKeywords, setPendingKeywords] = useState<string[]>([]); // Từ khóa được chọn tạm thời
  const [customers, setCustomers] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 10,
    totalPages: 1,
    total: 0,
  });
  const [searchQuery, setSearchQuery] = useState("");
  const [pendingSearchQuery, setPendingSearchQuery] = useState("");
  const [selectedCustomers, setSelectedCustomers] = useState<string[]>([]);
  const [isAllSelected, setIsAllSelected] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [customerToDelete, setCustomerToDelete] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [interestIds, setInterestIds] = useState<string[]>([]);

  // State cho GuestInfoModal
  const [isGuestInfoModalOpen, setIsGuestInfoModalOpen] = useState(false);
  const [editingCustomerId, setEditingCustomerId] = useState<string | null>(
    null
  );

  // Khởi tạo pendingKeywords từ selectedKeywords khi trang được tải
  useEffect(() => {
    setPendingKeywords(selectedKeywords);
  }, [selectedKeywords, setPendingKeywords]);
  // Biến cờ để theo dõi lần fetch đầu tiên và các lần fetch tiếp theo
  const _initialLoadRef = useRef({
    hasFetchedInitial: false,
    isInitializing: false,
  });

  // Biến để lưu trữ trang và trạng thái trước đó
  const oldPage = useRef(1);
  const oldSearchQuery = useRef("");
  const oldInterestIds = useRef<string[]>([]);

  // Sử dụng useRef để theo dõi trạng thái đã tải
  const hasInitialFetch = useRef(false);
  const loadingRef = useRef(false); // Prevent concurrent API calls
  // Helper function to convert keyword names to IDs
  const convertKeywordsToIds = async (
    keywords: string[]
  ): Promise<string[]> => {
    if (keywords.length === 0) {
      return [];
    }

    try {
      const interests = await interestService.getAllPublishedInterests();
      return interests
        .filter((interest) => keywords.includes(interest.name))
        .map((interest) => interest.id);
    } catch {
      toast.error("Không thể lấy danh sách từ khóa");
      return [];
    }
  };
  // Cache interests to avoid duplicate API calls
  const interestsCache = useRef<{ [key: string]: string }>({});
  const convertKeywordsToIdsFromCache = (keywords: string[]): string[] => {
    return keywords
      .map((keyword) => interestsCache.current[keyword])
      .filter(Boolean);
  };
  // Callback to populate cache when interests are loaded in KeywordFilter
  const handleInterestsLoaded = useCallback((interests: Interest[]) => {
    interests.forEach((interest) => {
      interestsCache.current[interest.name] = interest.id;
    });
  }, []);
  // Fetch customers from API
  const fetchCustomers = useCallback(async () => {
    // Prevent concurrent API calls
    if (loadingRef.current) return;

    try {
      loadingRef.current = true;
      setLoading(true);
      const response = await guestService.getGuestsWithInterests(
        pagination.page,
        pagination.limit,
        searchQuery || "",
        interestIds
      );

      // Đảm bảo không có dữ liệu trùng lặp bằng cách sử dụng Set với ID
      const uniqueCustomers = Array.from(
        new Map(response.data.map((item) => [item.id, item])).values()
      );

      setCustomers(uniqueCustomers);
      setPagination((prevPagination) => ({
        ...prevPagination,
        totalPages: response.total_pages,
        total: response.total,
      }));
    } catch {
      toast.error("Không thể tải danh sách khách hàng");
    } finally {
      setLoading(false);
      loadingRef.current = false;
    }
  }, [pagination.page, pagination.limit, searchQuery, interestIds]);

  useEffect(() => {
    // Chỉ fetch khi thay đổi page, searchQuery, interestIds hoặc chưa tải lần đầu
    if (
      !hasInitialFetch.current ||
      oldPage.current !== pagination.page ||
      oldSearchQuery.current !== searchQuery ||
      JSON.stringify(oldInterestIds.current) !== JSON.stringify(interestIds)
    ) {
      // Cập nhật các giá trị cũ
      oldPage.current = pagination.page;
      oldSearchQuery.current = searchQuery;
      oldInterestIds.current = [...interestIds];

      // Gọi API để lấy dữ liệu
      fetchCustomers();
      hasInitialFetch.current = true;
    }
  }, [pagination.page, searchQuery, interestIds, fetchCustomers]);
  // Effect to convert selected keyword names to IDs when they change
  useEffect(() => {
    const updateInterestIds = async () => {
      const newInterestIds = await convertKeywordsToIds(selectedKeywords);
      setInterestIds(newInterestIds);
    };

    updateInterestIds();
    // Lưu ý: Không gọi fetchCustomers ở đây để tránh gọi API nhiều lần
  }, [selectedKeywords]);

  // Select/deselect all customers
  const toggleSelectAll = () => {
    if (isAllSelected) {
      setSelectedCustomers([]);
    } else {
      setSelectedCustomers(customers.map((c) => c.id));
    }
    setIsAllSelected(!isAllSelected);
  };

  // Toggle selection of a single customer
  const toggleSelectCustomer = (id: string) => {
    if (selectedCustomers.includes(id)) {
      setSelectedCustomers(
        selectedCustomers.filter((customerId) => customerId !== id)
      );
      setIsAllSelected(false);
    } else {
      setSelectedCustomers([...selectedCustomers, id]);
      if (selectedCustomers.length + 1 === customers.length) {
        setIsAllSelected(true);
      }
    }
  };

  // Delete a customer or multiple customers
  const handleDeleteCustomer = async () => {
    setIsDeleting(true);
    try {
      if (selectedCustomers.length > 0) {
        // Delete multiple customers
        await guestService.deleteGuests(selectedCustomers);

        toast.success(
          `Đã xóa ${selectedCustomers.length} khách hàng thành công`
        );
        setSelectedCustomers([]); // Reset selected customers
        setIsAllSelected(false); // Reset select all state
      } else if (customerToDelete) {
        // Delete single customer
        await guestService.deleteGuest(customerToDelete);
        toast.success("Đã xóa khách hàng thành công");
        setCustomerToDelete(null); // Reset single customer to delete
      }
      // Refresh the customer list
      fetchCustomers();
    } catch (error) {
      toast.error("Không thể xóa khách hàng. Vui lòng thử lại.");
      console.error("Error deleting customer(s):", error);
    } finally {
      setIsDeleting(false);
      setDeleteConfirmOpen(false);
    }
  };

  // Export customers data
  const exportCustomersData = () => {
    // Implementation would depend on backend API
    toast.info("Tính năng xuất file đang được phát triển");
  };

  // Format birthday for display (backend returns ISO string)
  const formatBirthday = (dateString: string | null | undefined) => {
    if (!dateString) return "";
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    return date.getFullYear().toString();
  };

  // Navigate to specific page
  const goToPage = (page: number) => {
    if (page < 1 || page > pagination.totalPages) return;
    setPagination({ ...pagination, page });
  };

  // Handle customer delete action
  const handleCustomerDelete = (id: string) => {
    setCustomerToDelete(id);
    setDeleteConfirmOpen(true);
  };

  // Xử lý khi nhấn nút chỉnh sửa khách hàng
  const handleCustomerEdit = (id: string) => {
    setEditingCustomerId(id);
    setIsGuestInfoModalOpen(true);
  };

  // Xử lý khi modal chỉnh sửa đóng lại
  const handleModalClose = () => {
    setIsGuestInfoModalOpen(false);
    // Cập nhật lại danh sách khách hàng sau khi chỉnh sửa
    fetchCustomers();
  };

  return (
    <Suspense fallback={<LoadingScreen />}>
      <div className="flex-1 overflow-auto p-6">
        <h1 className="text-3xl font-bold mb-6">QUẢN LÍ KHÁCH HÀNG</h1>{" "}
        <div className="flex flex-col lg:flex-row items-start lg:items-center space-y-4 lg:space-y-0 lg:space-x-4 mb-6">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Button
                variant="outline"
                size="icon"
                className="h-10 w-10"
                disabled={selectedCustomers.length === 0}
                onClick={() => setDeleteConfirmOpen(true)}
              >
                <Trash2
                  className={`h-5 w-5 ${
                    selectedCustomers.length > 0
                      ? "text-red-500"
                      : "text-gray-500"
                  }`}
                />
              </Button>
              <div
                className={`absolute -top-2 -right-2 w-5 h-5 rounded-full ${
                  selectedCustomers.length > 0 ? "bg-red-500" : "bg-gray-300"
                } text-white flex items-center justify-center text-xs`}
              >
                {selectedCustomers.length}
              </div>
            </div>
            <Button
              variant="outline"
              className="space-x-2"
              onClick={exportCustomersData}
            >
              <Download className="h-4 w-4" />
              <span>Export file</span>
            </Button>
          </div>

          <div className="flex flex-col sm:flex-row flex-1 w-full items-start sm:items-center gap-2">
            <div className="flex-1 w-full">
              <Input
                type="text"
                placeholder="Tìm kiếm khách hàng..."
                value={pendingSearchQuery}
                onChange={(e) => setPendingSearchQuery(e.target.value)}
                className="w-full"
              />
            </div>{" "}
            <div className="w-full sm:w-auto sm:min-w-[250px] sm:max-w-[400px]">
              <KeywordFilter
                selectedKeywords={pendingKeywords}
                onChange={setPendingKeywords}
                onInterestsLoaded={handleInterestsLoaded}
              />
            </div>{" "}
            <Button
              onClick={async () => {
                // Tạo một bản sao của pagination với page = 1
                const newPagination = { ...pagination, page: 1 };

                // Try to use cached interests first, fallback to API call if cache is empty
                let newInterestIds: string[] = [];
                if (pendingKeywords.length > 0) {
                  // First try to use cached data
                  const cachedIds =
                    convertKeywordsToIdsFromCache(pendingKeywords);

                  if (cachedIds.length === pendingKeywords.length) {
                    // All keywords found in cache
                    newInterestIds = cachedIds;
                  } else {
                    // Need to fetch from API and update cache
                    try {
                      const interests =
                        await interestService.getAllPublishedInterests();
                      // Update cache
                      interests.forEach((interest) => {
                        interestsCache.current[interest.name] = interest.id;
                      });
                      // Get IDs for current keywords
                      newInterestIds = interests
                        .filter((interest) =>
                          pendingKeywords.includes(interest.name)
                        )
                        .map((interest) => interest.id);
                    } catch {
                      toast.error("Không thể lấy danh sách từ khóa");
                    }
                  }
                }

                // Cập nhật tất cả state trong một lần render
                // The useEffect will automatically trigger fetchCustomers when these values change
                setPagination(newPagination);
                setSearchQuery(pendingSearchQuery);
                setSelectedKeywords(pendingKeywords);
                setInterestIds(newInterestIds);
              }}
              className="bg-[#6366F1] text-white w-full sm:w-auto px-4"
            >
              <Search className="h-4 w-4 mr-0 sm:mr-2" />
              <span className="hidden sm:inline">Tìm kiếm</span>
            </Button>
          </div>
        </div>
        {/* Customer Table Component */}
        <CustomerTable
          customers={customers}
          loading={loading}
          selectedCustomers={selectedCustomers}
          toggleSelectCustomer={toggleSelectCustomer}
          toggleSelectAll={toggleSelectAll}
          isAllSelected={isAllSelected}
          onEdit={handleCustomerEdit}
          onDelete={handleCustomerDelete}
          formatBirthday={formatBirthday}
        />
        {/* Pagination Component */}
        {!loading && customers.length > 0 && (
          <CustomerPagination
            page={pagination.page}
            totalPages={pagination.totalPages}
            total={pagination.total}
            limit={pagination.limit}
            onPageChange={goToPage}
          />
        )}
      </div>

      {/* Delete confirmation dialog */}
      <Dialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-xl">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              Xác nhận xóa
            </DialogTitle>
            <DialogDescription>
              Bạn có chắc chắn muốn xóa
              {selectedCustomers.length > 1 ||
              (customerToDelete === null && selectedCustomers.length === 1)
                ? ` ${selectedCustomers.length} khách hàng`
                : " khách hàng này"}
              ? Hành động này không thể hoàn tác.
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
              onClick={handleDeleteCustomer}
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

      {/* GuestInfoModal for editing customer */}
      {editingCustomerId && (
        <GuestInfoModal
          open={isGuestInfoModalOpen}
          onOpenChange={handleModalClose}
          guestId={editingCustomerId}
        />
      )}
    </Suspense>
  );
}
