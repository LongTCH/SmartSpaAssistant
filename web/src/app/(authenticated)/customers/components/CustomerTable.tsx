"use client";

import { useState, useEffect, useRef } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Pencil,
  Trash2,
  Loader2,
  GripVertical,
  MessageSquare,
} from "lucide-react";
import { Conversation, Interest } from "@/types";
import { useRouter } from "next/navigation";

interface CustomerTableProps {
  customers: Conversation[];
  loading: boolean;
  selectedCustomers: string[];
  toggleSelectCustomer: (id: string) => void;
  toggleSelectAll: () => void;
  isAllSelected: boolean;
  onEdit?: (id: string) => void;
  onDelete: (id: string) => void;
  formatBirthday: (dateString: string) => string;
}

export function CustomerTable({
  customers,
  loading,
  selectedCustomers,
  toggleSelectCustomer,
  toggleSelectAll,
  isAllSelected,
  onEdit,
  onDelete,
  formatBirthday,
}: CustomerTableProps) {
  // Define column width type
  type ColumnWidths = {
    [key: string]: number;
    checkbox: number;
    name: number;
    gender: number;
    birthday: number;
    phone: number;
    email: number;
    address: number;
    interests: number;
    actions: number;
  };

  // Initial column widths
  const initialColumnWidths: ColumnWidths = {
    checkbox: 50,
    name: 200,
    gender: 100,
    birthday: 100,
    phone: 150,
    email: 200,
    address: 200,
    interests: 300,
    actions: 120,
  };

  // Add router for navigation to chat page
  const router = useRouter();

  // State to track which column is being resized
  const [resizingColumn, setResizingColumn] = useState<string | null>(null);
  // State to store column widths
  const [columnWidths, setColumnWidths] =
    useState<ColumnWidths>(initialColumnWidths);
  // Ref to store initial mouse position and width during resize
  const resizeStartRef = useRef({ x: 0, width: 0 });
  // Ref for the table container to detect overflow
  const tableContainerRef = useRef<HTMLDivElement>(null);

  // Trạng thái để lưu các hàng đang hiển thị tất cả nhãn
  const [_expandedRows, _setExpandedRows] = useState<Record<string, boolean>>(
    {}
  );

  // Function to navigate to conversations tab and select a specific guest
  const handleOpenChat = (guestId: string) => {
    // Sử dụng định dạng slug thay vì query parameter
    router.push(`/conversations/${guestId}`);
  };

  // Hàm để toggle hiển thị đầy đủ/thu gọn nhãn
  const _toggleExpandRow = (customerId: string) => {
    _setExpandedRows((prev) => ({
      ...prev,
      [customerId]: !prev[customerId],
    }));
  };

  // Hàm tính toán số lượng nhãn có thể hiển thị dựa theo chiều rộng cột và kích thước thực tế của từng nhãn
  const calculateVisibleTags = (columnWidth: number, interests: Interest[]) => {
    if (interests.length === 0) return 0;

    // Tạo một mảng để lưu trữ kích thước dự kiến của từng nhãn
    const tagWidths: number[] = [];
    const badgePaddingAndMargin = 20; // Padding (8px * 2) + Margin-right (4px) của badge
    const plusBadgeWidth = 40; // Chiều rộng ước tính của badge "+n"
    let totalWidth = 0;
    let visibleCount = 0;

    // Sử dụng DOM để đo kích thước thực tế của text
    const measureTextWidth = (
      text: string,
      font: string = "14px system-ui"
    ): number => {
      const canvas = document.createElement("canvas");
      const context = canvas.getContext("2d");
      if (context) {
        context.font = font;
        const metrics = context.measureText(text);
        return Math.ceil(metrics.width) + badgePaddingAndMargin;
      }
      return text.length * 8 + badgePaddingAndMargin; // Fallback nếu không thể đo
    };

    // Đo chiều rộng của từng nhãn
    interests.forEach((interest) => {
      const width = measureTextWidth(interest.name);
      tagWidths.push(width);
    });

    // Xác định số lượng nhãn có thể hiển thị
    for (let i = 0; i < tagWidths.length; i++) {
      // Dự đoán tổng chiều rộng nếu thêm nhãn này
      const projectedWidth = totalWidth + tagWidths[i];

      // Nếu còn đủ không gian hiển thị nhãn và không gian để chỉ báo "+n" (nếu cần)
      const needsPlusBadge = i < tagWidths.length - 1;
      const availableWidth = needsPlusBadge
        ? columnWidth - plusBadgeWidth
        : columnWidth;

      if (projectedWidth <= availableWidth) {
        totalWidth = projectedWidth;
        visibleCount++;
      } else {
        break;
      }
    }

    return Math.max(1, visibleCount); // Luôn hiển thị ít nhất 1 nhãn
  };

  // Hàm tính toán số lượng nhãn cho một khách hàng cụ thể
  const getVisibleTagsForCustomer = (customer: Conversation) => {
    return calculateVisibleTags(columnWidths.interests, customer.interests);
  };

  // State để lưu trữ số lượng nhãn hiển thị
  const [visibleTagsCount, setVisibleTagsCount] = useState(
    calculateVisibleTags(initialColumnWidths.interests, [])
  );

  // Cập nhật visibleTagsCount khi thay đổi kích thước cột
  useEffect(() => {
    // Tính toán lại số lượng nhãn hiển thị khi kích thước cột Interests thay đổi
    const updatedVisibleTags = calculateVisibleTags(columnWidths.interests, []);
    if (visibleTagsCount !== updatedVisibleTags) {
      setVisibleTagsCount(updatedVisibleTags);
    }
  }, [columnWidths.interests, visibleTagsCount]);

  // Track mouse movement during resize
  useEffect(() => {
    if (!resizingColumn) return;

    const handleMouseMove = (e: MouseEvent) => {
      const deltaX = e.clientX - resizeStartRef.current.x;
      const newWidth = Math.max(50, resizeStartRef.current.width + deltaX);

      setColumnWidths((prev) => ({
        ...prev,
        [resizingColumn]: newWidth,
      }));
    };

    const handleMouseUp = () => {
      setResizingColumn(null);
      document.body.style.cursor = "";
      document.body.classList.remove("resizing");
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);

    // Set cursor for entire document during resize
    document.body.style.cursor = "col-resize";
    document.body.classList.add("resizing");

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.classList.remove("resizing");
    };
  }, [resizingColumn]);

  // Start column resize
  const startResize = (e: React.MouseEvent, columnId: string) => {
    e.preventDefault();
    setResizingColumn(columnId);
    resizeStartRef.current = {
      x: e.clientX,
      width: columnWidths[columnId],
    };
  };

  return (
    <div className="border rounded-md overflow-hidden">
      <style jsx global>{`
        .excel-table-container {
          overflow-x: auto;
          position: relative;
        }

        .excel-table {
          table-layout: fixed;
          width: max-content;
          min-width: 100%;
          border-collapse: separate;
          border-spacing: 0;
        }

        .excel-table th,
        .excel-table td {
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .resize-handle {
          position: absolute;
          top: 0;
          right: 0;
          width: 5px;
          height: 100%;
          cursor: col-resize;
          background-color: transparent;
          z-index: 10;
          user-select: none;
        }

        .resize-handle:hover,
        .resize-handle.resizing {
          background-color: #6366f1;
        }

        .resizable-header {
          position: relative;
        }

        body.resizing {
          cursor: col-resize !important;
          user-select: none !important;
        }

        body.resizing * {
          user-select: none !important;
        }
      `}</style>

      <div className="excel-table-container" ref={tableContainerRef}>
        <Table className="excel-table">
          <TableHeader>
            <TableRow className="bg-gray-50">
              {/* Checkbox column */}
              <TableHead
                className="border-r resizable-header"
                style={{ width: columnWidths.checkbox + "px" }}
              >
                <div className="flex h-full items-center justify-center">
                  <Checkbox
                    checked={isAllSelected && customers.length > 0}
                    onCheckedChange={toggleSelectAll}
                    disabled={customers.length === 0}
                  />
                  <div
                    className={`resize-handle ${
                      resizingColumn === "checkbox" ? "resizing" : ""
                    }`}
                    onMouseDown={(e) => startResize(e, "checkbox")}
                  />
                </div>
              </TableHead>

              {/* Name column */}
              <TableHead
                className="text-[#6366F1] font-medium border-r resizable-header"
                style={{ width: columnWidths.name + "px" }}
              >
                <div className="flex items-center pl-4">Tên khách hàng</div>
                <div
                  className={`resize-handle ${
                    resizingColumn === "name" ? "resizing" : ""
                  }`}
                  onMouseDown={(e) => startResize(e, "name")}
                >
                  {(resizingColumn === "name" || !resizingColumn) && (
                    <div className="h-full w-full flex items-center justify-center">
                      {resizingColumn === "name" && (
                        <GripVertical className="h-4 w-4 text-white absolute pointer-events-none" />
                      )}
                    </div>
                  )}
                </div>
              </TableHead>

              {/* Gender column */}
              <TableHead
                className="text-[#6366F1] font-medium border-r resizable-header"
                style={{ width: columnWidths.gender + "px" }}
              >
                <div className="flex items-center pl-4">Giới tính</div>
                <div
                  className={`resize-handle ${
                    resizingColumn === "gender" ? "resizing" : ""
                  }`}
                  onMouseDown={(e) => startResize(e, "gender")}
                />
              </TableHead>

              {/* Birthday column */}
              <TableHead
                className="text-[#6366F1] font-medium border-r resizable-header"
                style={{ width: columnWidths.birthday + "px" }}
              >
                <div className="flex items-center pl-4">Năm sinh</div>
                <div
                  className={`resize-handle ${
                    resizingColumn === "birthday" ? "resizing" : ""
                  }`}
                  onMouseDown={(e) => startResize(e, "birthday")}
                />
              </TableHead>

              {/* Phone column */}
              <TableHead
                className="text-[#6366F1] font-medium border-r resizable-header"
                style={{ width: columnWidths.phone + "px" }}
              >
                <div className="flex items-center pl-4">SĐT</div>
                <div
                  className={`resize-handle ${
                    resizingColumn === "phone" ? "resizing" : ""
                  }`}
                  onMouseDown={(e) => startResize(e, "phone")}
                />
              </TableHead>

              {/* Email column */}
              <TableHead
                className="text-[#6366F1] font-medium border-r resizable-header"
                style={{ width: columnWidths.email + "px" }}
              >
                <div className="flex items-center pl-4">Email</div>
                <div
                  className={`resize-handle ${
                    resizingColumn === "email" ? "resizing" : ""
                  }`}
                  onMouseDown={(e) => startResize(e, "email")}
                />
              </TableHead>

              {/* Address column */}
              <TableHead
                className="text-[#6366F1] font-medium border-r resizable-header"
                style={{ width: columnWidths.address + "px" }}
              >
                <div className="flex items-center pl-4">Địa chỉ</div>
                <div
                  className={`resize-handle ${
                    resizingColumn === "address" ? "resizing" : ""
                  }`}
                  onMouseDown={(e) => startResize(e, "address")}
                />
              </TableHead>

              {/* Interests column */}
              <TableHead
                className="text-[#6366F1] font-medium border-r resizable-header"
                style={{ width: columnWidths.interests + "px" }}
              >
                <div className="flex items-center pl-4">Nhãn</div>
                <div
                  className={`resize-handle ${
                    resizingColumn === "interests" ? "resizing" : ""
                  }`}
                  onMouseDown={(e) => startResize(e, "interests")}
                />
              </TableHead>

              {/* Actions column */}
              <TableHead
                className="text-[#6366F1] font-medium text-right resizable-header"
                style={{ width: columnWidths.actions + "px" }}
              >
                <div className="flex items-center justify-end pr-4">
                  Thao tác
                </div>
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
            ) : customers.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={9}
                  className="h-24 text-center text-gray-500"
                >
                  Không có dữ liệu khách hàng
                </TableCell>
              </TableRow>
            ) : (
              customers.map((customer) => (
                <TableRow key={customer.id} className="hover:bg-gray-50">
                  <TableCell
                    className="border-r "
                    style={{ width: columnWidths.checkbox + "px" }}
                  >
                    <div className="flex h-full items-center justify-center">
                      <Checkbox
                        checked={selectedCustomers.includes(customer.id)}
                        onCheckedChange={() =>
                          toggleSelectCustomer(customer.id)
                        }
                      />
                    </div>
                  </TableCell>
                  <TableCell
                    className="border-r font-medium"
                    style={{ width: columnWidths.name + "px" }}
                  >
                    {customer.fullname}
                  </TableCell>
                  <TableCell
                    className="border-r"
                    style={{ width: columnWidths.gender + "px" }}
                  >
                    {customer.gender === "male"
                      ? "Nam"
                      : customer.gender === "female"
                      ? "Nữ"
                      : ""}
                  </TableCell>
                  <TableCell
                    className="border-r"
                    style={{ width: columnWidths.birthday + "px" }}
                  >
                    {formatBirthday(customer.birthday)}
                  </TableCell>
                  <TableCell
                    className="border-r"
                    style={{ width: columnWidths.phone + "px" }}
                  >
                    {customer.phone}
                  </TableCell>
                  <TableCell
                    className="border-r"
                    style={{ width: columnWidths.email + "px" }}
                  >
                    {customer.email}
                  </TableCell>
                  <TableCell
                    className="border-r truncate"
                    style={{ width: columnWidths.address + "px" }}
                    title={customer.address}
                  >
                    {customer.address}
                  </TableCell>
                  <TableCell
                    className="border-r"
                    style={{ width: columnWidths.interests + "px" }}
                    title={
                      customer.interests
                        ? customer.interests
                            .map((interest) => interest.name)
                            .join(", ")
                        : ""
                    }
                  >
                    <div className="flex flex-wrap items-center">
                      {customer.interests
                        ? customer.interests
                            .slice(0, getVisibleTagsForCustomer(customer))
                            .map((interest) => (
                              <Badge
                                key={interest.id}
                                className="mr-1 mb-1 inline-flex"
                                style={{
                                  backgroundColor: `${interest.color}20`, // 20% opacity
                                  color: interest.color,
                                  borderColor: `${interest.color}30`, // 30% opacity
                                }}
                              >
                                {interest.name}
                              </Badge>
                            ))
                        : null}
                      {customer.interests &&
                        customer.interests.length > 0 &&
                        customer.interests.length >
                          getVisibleTagsForCustomer(customer) && (
                          <Badge
                            className="mr-1 mb-1 inline-flex cursor-help"
                            style={{
                              backgroundColor: "#6366F120", // Màu chính với 20% opacity
                              color: "#6366F1",
                              borderColor: "#6366F130", // 30% opacity
                            }}
                            title={customer.interests
                              .slice(getVisibleTagsForCustomer(customer))
                              .map((interest) => interest.name)
                              .join(", ")}
                          >
                            +
                            {customer.interests.length -
                              getVisibleTagsForCustomer(customer)}
                          </Badge>
                        )}
                    </div>
                  </TableCell>
                  <TableCell
                    className="text-right"
                    style={{ width: columnWidths.actions + "px" }}
                  >
                    <div className="flex justify-end space-x-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleOpenChat(customer.id)}
                        title="Mở cuộc trò chuyện"
                      >
                        <MessageSquare className="h-4 w-4 text-indigo-500" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => onEdit && onEdit(customer.id)}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => onDelete(customer.id)}
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
    </div>
  );
}
