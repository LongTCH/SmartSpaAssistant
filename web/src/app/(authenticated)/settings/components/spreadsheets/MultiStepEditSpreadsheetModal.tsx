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
import { Sheet } from "@/types";
import { sheetService } from "@/services/api/sheet.service";
import { cn } from "@/lib/utils";

// Import specialized edit step components
import { EditSheetInfoStep } from "./steps/EditSheetInfoStep";
import { EditTableConfigStep } from "./steps/EditTableConfigStep";
import { ColumnConfig } from "@/types";

// Constants
const STEPS = {
  INFO: 1,
  COLUMNS: 2,
};

const STEP_TITLES = {
  [STEPS.INFO]: "Thông tin bảng tính",
  [STEPS.COLUMNS]: "Mô tả cột",
};

const TOTAL_STEPS = Object.keys(STEPS).length;

// Types
interface _SheetColumnConfig {
  name: string;
  dataType: string;
  description: string;
  isIndex: boolean;
  originalName: string;
}

interface MultiStepEditSpreadsheetModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  sheet: Sheet | null;
  onSuccess?: () => void;
}

export function MultiStepEditSpreadsheetModal({
  open,
  onOpenChange,
  sheet,
  onSuccess,
}: MultiStepEditSpreadsheetModalProps) {
  // Basic state
  const [currentStep, setCurrentStep] = useState(STEPS.INFO);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Step 1 data - Basic sheet info
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<"published" | "draft">("published");

  // Step 2 data - Column configurations
  const [columnConfigs, setColumnConfigs] = useState<ColumnConfig[]>([]);

  // Initialize form with sheet data when opened
  useEffect(() => {
    if (open && sheet) {
      // Reset to first step
      setCurrentStep(STEPS.INFO);

      // Populate form with current sheet data
      setName(sheet.name);
      setDescription(sheet.description || "");
      setStatus(sheet.status as "published" | "draft");

      // Initial column configs from existing sheet schema
      if (sheet.column_config) {
        try {
          // Đảm bảo rằng dữ liệu từ API được sử dụng trực tiếp mà không cần chuyển đổi
          setColumnConfigs(sheet.column_config);
        } catch {
          setColumnConfigs([]);
        }
      }
    } else if (!open) {
      // Reset state when modal closes
      resetForm();
    }
  }, [open, sheet]);

  // Reset form to initial state
  const resetForm = () => {
    setCurrentStep(STEPS.INFO);
    setName("");
    setDescription("");
    setStatus("published");
    setColumnConfigs([]);
  };

  // Update column configuration - allow description updates
  const updateColumnConfig = (index: number, field: string, value: any) => {
    // Allow updates for description field
    if (field === "description") {
      setColumnConfigs((prev) => {
        const newConfigs = [...prev];
        newConfigs[index] = {
          ...newConfigs[index],
          [field]: value,
        };
        return newConfigs;
      });
    }
  };

  // Form validation
  const validateCurrentStep = (): boolean => {
    switch (currentStep) {
      case STEPS.INFO:
        if (!name.trim()) {
          toast.error("Vui lòng nhập tên bảng tính");
          return false;
        }
        if (!description.trim()) {
          toast.error("Vui lòng nhập mô tả bảng tính");
          return false;
        }
        return true;
      default:
        return true;
    }
  };

  // Handle next step
  const handleNextStep = () => {
    if (!validateCurrentStep()) return;
    setCurrentStep((prev) => Math.min(prev + 1, TOTAL_STEPS));
  };

  // Handle previous step
  const handlePrevStep = () => {
    setCurrentStep((prev) => Math.max(prev - 1, STEPS.INFO));
  };

  // Convert internal column configs to API format
  const convertColumnConfigsToAPIFormat = (): ColumnConfig[] => {
    // Không cần chuyển đổi vì đã sử dụng đúng cấu trúc API
    return columnConfigs;
  };

  // Handle final submission
  const handleComplete = async () => {
    if (!sheet?.id) {
      toast.error("ID bảng tính không hợp lệ");
      return;
    }

    if (!validateCurrentStep()) return;

    setIsSubmitting(true);
    try {
      const apiColumnConfigs = convertColumnConfigsToAPIFormat();

      await sheetService.updateSheet(
        sheet.id,
        name,
        description,
        status,
        apiColumnConfigs
      );

      toast.success("Cập nhật bảng tính thành công");
      onOpenChange(false);
      onSuccess?.();
    } catch {
      toast.error("Có lỗi xảy ra khi cập nhật bảng tính");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Get current step component
  const getStepContent = () => {
    switch (currentStep) {
      case STEPS.INFO:
        return (
          <EditSheetInfoStep
            name={name}
            setName={setName}
            description={description}
            setDescription={setDescription}
            status={status}
            setStatus={setStatus}
          />
        );
      case STEPS.COLUMNS:
        return (
          <EditTableConfigStep
            columnConfigs={columnConfigs}
            updateColumnConfig={updateColumnConfig}
            descriptionOnly={true}
          />
        );
      default:
        return null;
    }
  };

  // Get step title
  const getStepTitle = () => {
    switch (currentStep) {
      case STEPS.INFO:
        return STEP_TITLES[STEPS.INFO];
      case STEPS.COLUMNS:
        return STEP_TITLES[STEPS.COLUMNS];
      default:
        return "";
    }
  };

  // Step indicator component
  const _StepIndicator = ({ currentStep }: { currentStep: number }) => {
    return (
      <div className="flex justify-center space-x-2 mb-6">
        {[1, 2, 3].map((step) => (
          <div
            key={step}
            className={cn(
              "w-3 h-3 rounded-full bg-gray-300",
              currentStep === step && "bg-primary",
              currentStep > step && "bg-green-500"
            )}
          />
        ))}
      </div>
    );
  };

  // Loading spinner component
  const LoadingSpinner = () => (
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
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[90vw] max-h-screen overflow-auto">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold text-center">
            Chỉnh sửa bảng tính - {getStepTitle()}
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
            <div className="text-xs font-medium ml-2">Mô tả cột</div>
          </div>
        </div>

        <div className="min-h-[300px]">{getStepContent()}</div>

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

          {currentStep < TOTAL_STEPS ? (
            <Button
              className="bg-blue-600 hover:bg-blue-700 text-white"
              onClick={handleNextStep}
            >
              Next
            </Button>
          ) : (
            <Button
              className="bg-green-600 hover:bg-green-700 text-white"
              onClick={handleComplete}
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <span className="flex items-center">
                  <LoadingSpinner />
                  Đang cập nhật...
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
