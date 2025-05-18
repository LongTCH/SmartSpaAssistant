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
interface NotificationTableProps {
  ITEMS_PER_PAGE: number;
  notifications: Notification[];
  isLoading: boolean;
  status: string;
  selectedNotificationIds: Set<string>;
  allCurrentPageSelected: boolean;
  handleSelectNotification: (id: string, checked: boolean) => void;
  handleSelectAllOnPage: (checked: boolean) => void;
  handleEdit: (notification: Notification) => void;
  openDeleteConfirmationForSingle: (id: string) => void;
}

export function NotificationTable({
  ITEMS_PER_PAGE,
  notifications,
  isLoading,
  status,
  selectedNotificationIds,
  allCurrentPageSelected,
  handleSelectNotification,
  handleSelectAllOnPage,
  handleEdit,
  openDeleteConfirmationForSingle,
}: NotificationTableProps) {
  return (
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
                        }"`}
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
  );
}
