"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import { ExcelData } from "@/types";
import { sheetService } from "@/services/api/sheet.service";
import { ColumnConfig } from "@/types";

// Import step components
import { SheetInfoStep } from "./steps/SheetInfoStep";
import { UploadStep } from "./steps/UploadStep";
import { TableConfigStep } from "./steps/TableConfigStep";
import { PreviewStep } from "./steps/PreviewStep";

interface MultiStepAddSpreadsheetModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function MultiStepAddSpreadsheetModal({
  open,
  onOpenChange,
  onSuccess,
}: MultiStepAddSpreadsheetModalProps) {
  // Basic state
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Step 1 data
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<"published" | "draft">("published");

  // Step 2 data
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Step 3 data
  const [columnConfigs, setColumnConfigs] = useState<ColumnConfig[]>([]);

  // Step 4 preview data
  const [excelData, setExcelData] = useState<ExcelData | null>(null);
  const [allRows, setAllRows] = useState<any[][]>([]);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const rowsPerPage = 10;

  // Tính toán dữ liệu hiển thị dựa trên allRows và phân trang
  const getVisibleRows = () => {
    if (!excelData || !allRows.length) return [];
    return allRows.slice(0, Math.min(allRows.length, rowsPerPage));
  };

  // Reset state when modal closes
  useEffect(() => {
    if (!open) {
      setCurrentStep(1);
      setName("");
      setDescription("");
      setStatus("published");
      setSelectedFile(null);
      setColumnConfigs([]);
      setExcelData(null);
      setAllRows([]);
    }
  }, [open]);

  // Load more rows when needed
  const loadMoreRows = () => {
    if (!excelData) return;

    setIsLoadingMore(true);

    const currentlyDisplayed = excelData.rows.length;
    const nextBatchSize = Math.min(
      rowsPerPage,
      allRows.length - currentlyDisplayed
    );

    if (nextBatchSize <= 0) {
      setIsLoadingMore(false);
      return;
    }

    // Update displayed data with next batch
    const nextRows = [
      ...excelData.rows,
      ...allRows.slice(currentlyDisplayed, currentlyDisplayed + nextBatchSize),
    ];

    setExcelData({
      ...excelData,
      rows: nextRows,
    });

    setIsLoadingMore(false);
  };

  // Handle scroll event for lazy loading
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    if (!excelData) return;

    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;

    // If scrolled near bottom and not already loading
    if (
      scrollHeight - scrollTop - clientHeight < 20 &&
      !isLoadingMore &&
      excelData.rows.length < allRows.length
    ) {
      loadMoreRows();
    }
  };

  // Update column configuration
  const updateColumnConfig = (index: number, field: string, value: any) => {
    setColumnConfigs((prev) => {
      const newConfigs = [...prev];
      newConfigs[index] = {
        ...newConfigs[index],
        [field]: value,
      };
      return newConfigs;
    });
  };

  // Handle next step
  const handleNextStep = () => {
    if (currentStep === 1) {
      // Validate step 1
      if (!name.trim()) {
        toast.error("Vui lòng nhập tên bảng tính");
        return;
      }
      if (!description.trim()) {
        toast.error("Vui lòng nhập mô tả bảng tính");
        return;
      }
    } else if (currentStep === 2) {
      // Validate step 2
      if (!selectedFile) {
        toast.error("Vui lòng tải lên file Excel");
        return;
      }
      if (!excelData || excelData.rows.length === 0) {
        toast.error(
          "Dữ liệu Excel không hợp lệ hoặc trống. Vui lòng kiểm tra lại."
        );
        return;
      }
      if (columnConfigs.length === 0 || !excelData) {
        toast.error("Vui lòng chờ xử lý file hoàn tất");
        return;
      }
    }

    setCurrentStep((prev) => Math.min(prev + 1, 4));
  };

  // Handle previous step
  const handlePrevStep = () => {
    setCurrentStep((prev) => Math.max(prev - 1, 1));
  };

  // Convert internal column configs to API format
  const convertColumnConfigsToAPIFormat = (): ColumnConfig[] => {
    return columnConfigs.map((config) => ({
      column_name: config.column_name,
      column_type: config.column_type,
      description: config.description,
      is_index: config.is_index || false,
    }));
  };

  // Handle final submission
  const handleComplete = async () => {
    if (!selectedFile) {
      toast.error("Không tìm thấy file Excel");
      return;
    }

    // Kiểm tra dữ liệu đầu vào
    if (!name.trim()) {
      toast.error("Vui lòng nhập tên bảng tính");
      return;
    }

    setIsSubmitting(true);
    try {
      // Convert column configs to API format
      const apiColumnConfigs = convertColumnConfigsToAPIFormat();

      // Call API to upload sheet with column configurations
      await sheetService.uploadSheet(
        name,
        description,
        status,
        selectedFile,
        apiColumnConfigs
      );

      toast.success("Lưu bảng tính thành công");

      // Close modal and call success callback if provided
      onOpenChange(false);
      if (onSuccess) onSuccess();
    } catch (error: any) {
      toast.error(
        error?.response?.data?.message || "Có lỗi xảy ra khi lưu bảng tính"
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  // Get current step component
  const getStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <SheetInfoStep
            name={name}
            setName={setName}
            description={description}
            setDescription={setDescription}
            status={status}
            setStatus={setStatus}
          />
        );
      case 2:
        return (
          <UploadStep
            selectedFile={selectedFile}
            setSelectedFile={setSelectedFile}
            setColumnConfigs={setColumnConfigs}
            setExcelData={setExcelData}
            setAllRows={setAllRows} // Add this missing prop
            isLoading={isLoading}
            setIsLoading={setIsLoading}
          />
        );
      case 3:
        return (
          <TableConfigStep
            columnConfigs={columnConfigs}
            updateColumnConfig={updateColumnConfig}
            excelData={excelData}
          />
        );
      case 4:
        return (
          <PreviewStep
            excelData={excelData}
            columnConfigs={columnConfigs}
            visibleRows={excelData?.rows || []}
            allRows={allRows}
            isLoadingMore={isLoadingMore}
            handleScroll={handleScroll}
            loadMoreRows={loadMoreRows}
          />
        );
      default:
        return null;
    }
  };

  // Get step title
  const getStepTitle = () => {
    switch (currentStep) {
      case 1:
        return "Thông tin bảng";
      case 2:
        return "Upload";
      case 3:
        return "Cấu hình bảng";
      case 4:
        return "Preview";
      default:
        return "";
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[90vw] max-h-screen overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold text-center">
            Thêm bảng tính - {getStepTitle()}
          </DialogTitle>
        </DialogHeader>

        {/* Step indicators */}
        <div className="w-full flex justify-center items-center py-6">
          <div className="flex items-center">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center ${
                currentStep >= 1
                  ? "bg-[#0F62FE] text-white"
                  : "bg-gray-200 text-gray-500"
              }`}
            >
              1
            </div>
            <div className="text-xs font-medium ml-2 mr-3">Thông tin bảng</div>
          </div>
          <div
            className={`w-12 h-0.5 mx-1 ${
              currentStep > 1 ? "bg-[#0F62FE]" : "bg-gray-200"
            }`}
          ></div>
          <div className="flex items-center">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center ${
                currentStep >= 2
                  ? "bg-[#0F62FE] text-white"
                  : "bg-gray-200 text-gray-500"
              }`}
            >
              2
            </div>
            <div className="text-xs font-medium ml-2 mr-3">Upload</div>
          </div>
          <div
            className={`w-12 h-0.5 mx-1 ${
              currentStep > 2 ? "bg-[#0F62FE]" : "bg-gray-200"
            }`}
          ></div>
          <div className="flex items-center">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center ${
                currentStep >= 3
                  ? "bg-[#0F62FE] text-white"
                  : "bg-gray-200 text-gray-500"
              }`}
            >
              3
            </div>
            <div className="text-xs font-medium ml-2 mr-3">Cấu hình bảng</div>
          </div>
          <div
            className={`w-12 h-0.5 mx-1 ${
              currentStep > 3 ? "bg-[#0F62FE]" : "bg-gray-200"
            }`}
          ></div>
          <div className="flex items-center">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center ${
                currentStep >= 4
                  ? "bg-[#0F62FE] text-white"
                  : "bg-gray-200 text-gray-500"
              }`}
            >
              4
            </div>
            <div className="text-xs font-medium ml-2">Preview</div>
          </div>
        </div>

        {/* Step content */}
        <div
          className="overflow-y-auto flex-grow"
          style={{ maxHeight: "calc(90vh - 200px)", backgroundColor: "white" }}
        >
          {getStepContent()}
        </div>

        {/* Footer buttons */}
        <DialogFooter className="flex-shrink-0 border-t pt-4 mt-4">
          {currentStep > 1 && (
            <Button
              variant="outline"
              onClick={handlePrevStep}
              disabled={isSubmitting}
            >
              Previous
            </Button>
          )}

          {currentStep < 4 ? (
            <Button
              className="bg-blue-600 hover:bg-blue-700 text-white"
              onClick={handleNextStep}
              disabled={currentStep === 2 && isLoading}
            >
              {currentStep === 2 && isLoading ? "Đang xử lý..." : "Next"}
            </Button>
          ) : (
            <Button
              className="bg-green-600 hover:bg-green-700 text-white"
              onClick={handleComplete}
              disabled={isSubmitting}
            >
              {isSubmitting ? (
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
                  Đang hoàn thành...
                </span>
              ) : (
                "Complete"
              )}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
