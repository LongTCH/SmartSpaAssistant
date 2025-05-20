"use client";

import { useState, useEffect, useCallback, useMemo } from "react"; // Add useMemo
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter } from "@/components/ui/dialog";
import { toast } from "sonner";
import { notificationService } from "@/services/api/notification.service";
import { NotificationData, NotificationParams } from "@/types";

// Import step components
import { InfoStep } from "./steps/InfoStep";
import { ConfigStep } from "./steps/ConfigStep";
import { DialogTitle } from "@radix-ui/react-dialog";

// Create an adapter type to map between NotificationParams and Parameter
// This is needed because ConfigStep expects Parameter type
interface Parameter {
  id: string;
  name: string;
  type: string;
  description: string;
}

interface MultiStepAddNotificationModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function MultiStepAddNotificationModal({
  open,
  onOpenChange,
  onSuccess,
}: MultiStepAddNotificationModalProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Default parameters for reference - wrapped in useMemo
  const defaultParameters = useMemo<Parameter[]>(
    () => [
      {
        id: "1",
        name: "customer_name",
        type: "String",
        description: "Tên khách hàng đặt hàng",
      },
      {
        id: "2",
        name: "customer_phone",
        type: "String",
        description: "Số điện thoại khách đặt hàng",
      },
      {
        id: "3",
        name: "customer_address",
        type: "String",
        description: "Địa chỉ khách đặt giao hàng",
      },
      {
        id: "4",
        name: "order_detail",
        type: "String",
        description: "Danh sách sản phẩm bao gồm Tên sp, số lượng",
      },
      {
        id: "5",
        name: "total_money",
        type: "Numeric",
        description: "Tổng giá trị đơn hàng (đã trừ khuyến mãi)",
      },
    ],
    [] // Empty dependency array since these don't change
  );

  // Default content with template variables
  const defaultContent = useMemo(
    () => `Bạn có đơn hàng cần xác nhận:
Khách: {{ customer_name }}
SĐT: {{ customer_phone }}
Địa chỉ: {{ customer_address }}
Chi tiết đơn hàng:
{{ order_detail }}
Tổng tiền: {{ total_money }} VND`,
    [] // Empty dependency array
  );

  // Initialize form with default values
  const [formName, setFormName] = useState("");
  const [formStatus, setFormStatus] = useState<"published" | "draft">(
    "published"
  );
  const [formColor, setFormColor] = useState("#2196F3");
  const [formUseCase, setFormUseCase] = useState("");
  const [formContent, setFormContent] = useState(defaultContent);
  const [formParameters, setFormParameters] = useState<Parameter[]>([
    ...defaultParameters,
  ]);

  // Generate a unique ID for new parameters
  const generateId = () => {
    return Date.now().toString();
  };

  // Add new parameter
  const addParameter = () => {
    const newParameter: Parameter = {
      id: generateId(),
      name: "",
      type: "String",
      description: "",
    };

    setFormParameters([...formParameters, newParameter]);
  };

  // Update parameter
  const updateParameter = (
    id: string,
    field: keyof Parameter,
    value: string
  ) => {
    setFormParameters(
      formParameters.map((param) =>
        param.id === id ? { ...param, [field]: value } : param
      )
    );
  };

  // Delete parameter
  const deleteParameter = (id: string) => {
    setFormParameters(formParameters.filter((param) => param.id !== id));
  };

  // Reset the form to initial values
  const resetForm = useCallback(() => {
    setCurrentStep(1);
    setIsSubmitting(false);
    setFormName("");
    setFormStatus("published");
    setFormColor("#2196F3");
    setFormUseCase("");
    setFormContent(defaultContent);
    setFormParameters([...defaultParameters]);
  }, [defaultContent, defaultParameters]); // Add dependencies

  // Reset form when modal closes
  useEffect(() => {
    if (!open) {
      resetForm();
    }
  }, [open, resetForm]);

  // Navigation functions
  const handleNext = () => {
    // Validate current step before proceeding
    if (currentStep === 1) {
      if (!formName.trim() || !formUseCase.trim()) {
        toast.error("Vui lòng điền đầy đủ thông tin cơ bản");
        return;
      }
    }
    setCurrentStep(currentStep + 1);
  };

  const handleBack = () => {
    setCurrentStep(currentStep - 1);
  };

  // Handle form submission
  const handleSubmit = async () => {
    // Parameter validation
    const validNameRegex = /^[a-zA-Z_][a-zA-Z0-9_]*$/;
    for (const param of formParameters) {
      if (!param.name.trim()) {
        toast.error(
          `Tên của một trong các tham số không được để trống. Vui lòng điền tên hoặc xóa tham số nếu không cần thiết.`
        );
        return;
      }
      if (!validNameRegex.test(param.name)) {
        toast.error(
          `Tên tham số "${param.name}" không hợp lệ. Tên chỉ nên chứa chữ cái, số, dấu gạch dưới và không bắt đầu bằng số.`
        );
        return;
      }
    }

    try {
      setIsSubmitting(true);

      // Convert parameters to the API format
      const apiParams: NotificationParams[] = formParameters.map(
        (param, index) => ({
          index: index,
          param_name: param.name,
          param_type: param.type,
          description: param.description,
        })
      );

      // Create notification data object
      const notificationData: NotificationData = {
        label: formName,
        description: formUseCase,
        status: formStatus,
        color: formColor,
        params: apiParams,
        content: formContent || null,
      };

      // Call API to create notification
      await notificationService.createNotification(notificationData);

      // Success message and cleanup
      toast.success("Tạo thông báo mới thành công");
      onOpenChange(false);
      if (onSuccess) onSuccess();
    } catch {
      toast.error("Có lỗi xảy ra khi tạo thông báo mới");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Define steps
  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <InfoStep
            name={formName}
            setName={setFormName}
            description={formUseCase}
            setDescription={setFormUseCase}
            color={formColor}
            setColor={setFormColor}
            status={formStatus}
            setStatus={setFormStatus}
          />
        );
      case 2:
        return (
          <ConfigStep
            parameters={formParameters}
            addParameter={addParameter}
            updateParameter={updateParameter}
            deleteParameter={deleteParameter}
            content={formContent}
            setContent={setFormContent}
          />
        );
      default:
        return null;
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTitle></DialogTitle>
      <DialogContent className="sm:max-w-[90vw] max-h-screen overflow-auto flex flex-col">
        {/* Step indicators */}
        <div className="w-full flex justify-center items-center py-6">
          {/* Step 1: Info */}
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
            <div className="text-xs font-medium ml-2 mr-3">Thông tin</div>
          </div>
          <div
            className={`w-12 h-0.5 mx-1 ${
              currentStep > 1 ? "bg-[#0F62FE]" : "bg-gray-200"
            }`}
          ></div>
          {/* Step 2: Config */}
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
            <div className="text-xs font-medium ml-2">Cấu hình</div>
          </div>
        </div>

        {renderStep()}

        <DialogFooter className="mt-6 flex justify-between">
          {currentStep > 1 ? (
            <Button
              variant="outline"
              onClick={handleBack}
              disabled={isSubmitting}
            >
              Quay lại
            </Button>
          ) : (
            <div></div>
          )}

          <div className="space-x-2">
            {currentStep === 1 && (
              <Button
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isSubmitting}
              >
                Hủy
              </Button>
            )}

            {currentStep < 2 ? (
              <Button
                onClick={handleNext}
                disabled={isSubmitting}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                Tiếp tục
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="bg-green-600 hover:bg-green-700 text-white"
              >
                {isSubmitting ? "Đang tạo..." : "Tạo thông báo"}
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
