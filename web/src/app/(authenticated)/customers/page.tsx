"use client";

import { useState, useEffect, Suspense } from "react";
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
  Download,
  ChevronLeft,
  ChevronRight,
  Pencil,
  Trash2,
  Search,
  Loader2,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { KeywordFilter } from "./components/KeywordFilter";
import { LoadingScreen } from "@/components/loading-screen";
import { guestService } from "@/services/api/guest.service";
import { GuestInfo } from "@/types";
import { toast } from "sonner";
import { Dialog, DialogContent } from "@/components/ui/dialog";

export default function CustomerManagement() {
  const [selectedKeywords, setSelectedKeywords] = useState<string[]>([]);
  const [customers, setCustomers] = useState<GuestInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 10,
    totalPages: 1,
    total: 0,
  });
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCustomers, setSelectedCustomers] = useState<string[]>([]);
  const [isAllSelected, setIsAllSelected] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [customerToDelete, setCustomerToDelete] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Fetch customers from API
  useEffect(() => {
    fetchCustomers();
  }, [pagination.page, pagination.limit]);

  const fetchCustomers = async () => {
    try {
      setLoading(true);
      const response = await guestService.getGuestsWithInterests(
        pagination.page,
        pagination.limit
      );
      setCustomers(response.data);
      setPagination({
        ...pagination,
        totalPages: response.total_pages,
        total: response.total,
      });
    } catch (error) {
      console.error("Error fetching customers:", error);
      toast.error("Không thể tải danh sách khách hàng");
    } finally {
      setLoading(false);
    }
  };

  // Search functionality - applied client-side for now
  const filteredCustomers = customers.filter((customer) => {
    // Filter by search query across multiple fields
    const matchesSearch =
      !searchQuery ||
      customer.fullname.toLowerCase().includes(searchQuery.toLowerCase()) ||
      customer.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      customer.phone.toLowerCase().includes(searchQuery.toLowerCase());

    // Filter by selected keywords/interests
    const matchesKeywords =
      selectedKeywords.length === 0 ||
      customer.interests.some((interest) =>
        selectedKeywords.includes(interest.name)
      );

    return matchesSearch && matchesKeywords;
  });

  // Pagination navigation
  const goToPage = (page: number) => {
    if (page < 1 || page > pagination.totalPages) return;
    setPagination({ ...pagination, page });
  };

  // Select/deselect all customers
  const toggleSelectAll = () => {
    if (isAllSelected) {
      setSelectedCustomers([]);
    } else {
      setSelectedCustomers(filteredCustomers.map((c) => c.id));
    }
    setIsAllSelected(!isAllSelected);
  };

  // Toggle selection of a single customer
  const toggleSelectCustomer = (id: string) => {
    if (selectedCustomers.includes(id)) {
      setSelectedCustomers(selectedCustomers.filter((customerId) => customerId !== id));
      setIsAllSelected(false);
    } else {
      setSelectedCustomers([...selectedCustomers, id]);
      if (selectedCustomers.length + 1 === filteredCustomers.length) {
        setIsAllSelected(true);
      }
    }
  };

  // Delete a customer
  const handleDeleteCustomer = async () => {
    if (!customerToDelete) return;
    
    setIsDeleting(true);
    try {
      // Replace with actual API call when available
      // await guestService.deleteGuest(customerToDelete);
      toast.success("Đã xóa khách hàng thành công");
      
      // Update UI by removing deleted customer
      setCustomers(customers.filter(c => c.id !== customerToDelete));
      setSelectedCustomers(selectedCustomers.filter(id => id !== customerToDelete));
      
      setDeleteConfirmOpen(false);
      setCustomerToDelete(null);
    } catch (error) {
      console.error("Error deleting customer:", error);
      toast.error("Không thể xóa khách hàng");
    } finally {
      setIsDeleting(false);
    }
  };

  // Export customers data
  const exportCustomersData = () => {
    // Implementation would depend on backend API
    toast.info("Tính năng xuất file đang được phát triển");
  };

  // Format birthday for display (backend returns ISO string)
  const formatBirthday = (dateString: string) => {
    if (!dateString) return "";
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    return date.getFullYear().toString();
  };

  return (
    <Suspense fallback={<LoadingScreen />}>
      <div className="flex-1 overflow-auto p-6">
        <h1 className="text-3xl font-bold mb-6">QUẢN LÍ KHÁCH HÀNG</h1>

        <div className="flex items-center space-x-4 mb-6">
          <div className="relative">
            <div className="absolute -top-2 -right-2 w-5 h-5 rounded-full bg-red-500 text-white flex items-center justify-center text-xs">
              {selectedCustomers.length}
            </div>
            <Button 
              variant="outline" 
              size="icon" 
              className="h-10 w-10"
              disabled={selectedCustomers.length === 0}
              onClick={() => setDeleteConfirmOpen(true)}
            >
              <Trash2 className="h-5 w-5 text-gray-500" />
            </Button>
          </div>
          <Button 
            variant="outline" 
            className="space-x-2"
            onClick={exportCustomersData}
          >
            <Download className="h-4 w-4" />
            <span>Export file</span>
          </Button>

          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input 
              placeholder="Search..." 
              className="pl-10" 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <KeywordFilter
            selectedKeywords={selectedKeywords}
            setSelectedKeywords={setSelectedKeywords}
          />
        </div>

        <div className="border rounded-md">
          <Table>
            <TableHeader>
              <TableRow className="bg-gray-50">
                <TableHead className="w-12">
                  <Checkbox 
                    checked={isAllSelected && filteredCustomers.length > 0} 
                    onCheckedChange={toggleSelectAll}
                  />
                </TableHead>
                <TableHead className="text-[#6366F1] font-medium">
                  Tên khách hàng
                </TableHead>
                <TableHead className="text-[#6366F1] font-medium">
                  Giới tính
                </TableHead>
                <TableHead className="text-[#6366F1] font-medium">
                  Năm sinh
                </TableHead>
                <TableHead className="text-[#6366F1] font-medium">
                  SĐT
                </TableHead>
                <TableHead className="text-[#6366F1] font-medium">
                  Email
                </TableHead>
                <TableHead className="text-[#6366F1] font-medium">
                  Địa chỉ
                </TableHead>
                <TableHead className="text-[#6366F1] font-medium">
                  Xu hướng
                </TableHead>
                <TableHead className="text-[#6366F1] font-medium text-right">
                  Thao tác
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={9} className="h-24 text-center">
                    <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                    <div className="mt-2">Đang tải dữ liệu...</div>
                  </TableCell>
                </TableRow>
              ) : filteredCustomers.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="h-24 text-center text-gray-500">
                    Không có dữ liệu khách hàng
                  </TableCell>
                </TableRow>
              ) : (
                filteredCustomers.map((customer) => (
                  <TableRow key={customer.id}>
                    <TableCell>
                      <Checkbox 
                        checked={selectedCustomers.includes(customer.id)}
                        onCheckedChange={() => toggleSelectCustomer(customer.id)}
                      />
                    </TableCell>
                    <TableCell>{customer.fullname}</TableCell>
                    <TableCell>{customer.gender}</TableCell>
                    <TableCell>{formatBirthday(customer.birthday)}</TableCell>
                    <TableCell>{customer.phone}</TableCell>
                    <TableCell>{customer.email}</TableCell>
                    <TableCell className="max-w-xs truncate">
                      {customer.address}
                    </TableCell>
                    <TableCell>
                      {customer.interests.map(interest => interest.name).join(", ")}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end space-x-2">
                        <Button variant="ghost" size="icon">
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="icon"
                          onClick={() => {
                            setCustomerToDelete(customer.id);
                            setDeleteConfirmOpen(true);
                          }}
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {!loading && filteredCustomers.length > 0 && (
          <div className="flex justify-center items-center mt-6 space-x-2">
            <Button 
              variant="outline" 
              size="icon" 
              className="h-10 w-10"
              disabled={pagination.page === 1}
              onClick={() => goToPage(pagination.page - 1)}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            {Array.from({ length: pagination.totalPages }, (_, i) => i + 1).map((page) => (
              <Button 
                key={page}
                className={pagination.page === page ? "bg-[#6366F1] text-white h-10 w-10" : "variant-outline h-10 w-10"}
                onClick={() => goToPage(page)}
              >
                {page}
              </Button>
            ))}
            <Button 
              variant="outline" 
              size="icon" 
              className="h-10 w-10"
              disabled={pagination.page === pagination.totalPages}
              onClick={() => goToPage(pagination.page + 1)}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>

      {/* Delete confirmation dialog */}
      <Dialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <div className="p-6">
            <h2 className="text-xl font-semibold mb-4">Xác nhận xóa</h2>
            <p className="mb-6">Bạn có chắc chắn muốn xóa khách hàng này?</p>
            <div className="flex justify-end space-x-2">
              <Button 
                variant="outline" 
                onClick={() => setDeleteConfirmOpen(false)}
                disabled={isDeleting}
              >
                Hủy
              </Button>
              <Button 
                onClick={handleDeleteCustomer}
                disabled={isDeleting}
                className="bg-red-500 hover:bg-red-600 text-white"
              >
                {isDeleting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Đang xóa
                  </>
                ) : (
                  "Xóa"
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </Suspense>
  );
}
