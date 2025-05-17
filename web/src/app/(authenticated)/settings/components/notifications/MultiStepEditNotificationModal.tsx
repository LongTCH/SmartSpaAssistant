"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogTitle,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import { notificationService } from "@/services/api/notification.service";
import { Notification, NotificationData, NotificationParams } from "@/types";

// Import step components
import { InfoStep } from "./steps/InfoStep";
import { ConfigStep } from "./steps/ConfigStep";

// Create an adapter type to map between NotificationParams and Parameter
// This is needed because ConfigStep expects Parameter type
interface Parameter {
  id: string;
  name: string;
  type: string;
  description: string;
}

interface MultiStepEditNotificationModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  notification: Notification | null;
  onSuccess?: () => void;
}

export function MultiStepEditNotificationModal({
  open,
  onOpenChange,
  notification,
  onSuccess,
}: MultiStepEditNotificationModalProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Default parameters for reference
  const defaultParameters: Parameter[] = [];

  // Default content with template variables
  const defaultContent = ``;

  // Initialize form with existing notification or default values
  const [formName, setFormName] = useState(notification?.label || "");
  const [formStatus, setFormStatus] = useState<"published" | "draft">(
    notification?.status || "published"
  );
  const [formColor, setFormColor] = useState(notification?.color || "#2196F3");
  const [formUseCase, setFormUseCase] = useState(
    notification?.description || ""
  );
  const [formContent, setFormContent] = useState(
    notification?.content || defaultContent || ""
  );

  // Convert API parameters format to internal format
  const initialParams: Parameter[] = notification?.params
    ? notification.params.map((param) => ({
        id: param.index.toString(),
        name: param.param_name,
        type: param.param_type,
        description: param.description,
      }))
    : [...defaultParameters];

  const [formParameters, setFormParameters] =
    useState<Parameter[]>(initialParams);

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
    if (field === "name") {
      const validNameRegex = /^[a-zA-Z_][a-zA-Z0-9_]*$/;
      if (value && !validNameRegex.test(value)) {
        toast.error(
          "Tên tham số không hợp lệ. Chỉ sử dụng chữ cái, số và dấu gạch dưới, và không bắt đầu bằng số."
        );
        return;
      }
    }
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

  // Reset the form to initial values based on notification or defaults
  const resetForm = () => {
    setCurrentStep(1);
    setIsSubmitting(false);

    if (notification) {
      setFormName(notification.label);
      setFormStatus(notification.status);
      setFormColor(notification.color);
      setFormUseCase(notification.description);
      setFormContent(notification.content || defaultContent);

      const mappedParams =
        notification.params?.map((param) => ({
          id: param.index.toString(),
          name: param.param_name,
          type: param.param_type,
          description: param.description,
        })) || [];

      setFormParameters(
        mappedParams.length > 0 ? mappedParams : [...defaultParameters]
      );
    } else {
      setFormName("");
      setFormStatus("published");
      setFormColor("#2196F3");
      setFormUseCase("");
      setFormContent(defaultContent);
      setFormParameters([...defaultParameters]);
    }
  };

  // Reset form when modal closes or notification changes
  useEffect(() => {
    if (open && notification) {
      resetForm();
    }
  }, [open, notification]);

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
    if (!notification?.id) {
      toast.error("Không tìm thấy thông báo để cập nhật");
      return;
    }

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

      // Create notification object
      const updatedNotification: Notification = {
        ...notification,
        label: formName,
        description: formUseCase,
        status: formStatus,
        color: formColor,
        params: apiParams,
        content: formContent || null,
      };

      // Call API to update notification
      await notificationService.updateNotification(
        notification.id,
        updatedNotification
      );

      // Success message and cleanup
      toast.success("Cập nhật thông báo thành công");
      onOpenChange(false);
      if (onSuccess) onSuccess();
    } catch (error) {
      toast.error("Có lỗi xảy ra khi cập nhật thông báo");
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

  if (!notification) {
    return null;
  }

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
                {isSubmitting ? "Đang lưu..." : "Lưu thay đổi"}
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
