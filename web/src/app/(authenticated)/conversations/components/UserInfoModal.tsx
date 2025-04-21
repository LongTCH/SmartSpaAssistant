"use client";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { GuestInfo, GuestInfoUpdate } from "@/types";
import { Edit, RotateCcw } from "lucide-react";
import { useEffect, useState } from "react";
import { guestService } from "@/services/api/guest.service";
import { toast } from "sonner";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";

interface UserInfoModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  guestId: string;
}

export function UserInfoModal({
  open,
  onOpenChange,
  guestId,
}: UserInfoModalProps) {
  const [guestInfo, setGuestInfo] = useState<GuestInfo | null>(null);
  const [originalGuestInfo, setOriginalGuestInfo] = useState<GuestInfo | null>(
    null
  );
  const [editableFields, setEditableFields] = useState<Record<string, boolean>>(
    {
      fullname: false,
      gender: false,
      birthday: false,
      email: false,
      phone: false,
      address: false,
      skinCondition: false,
    }
  );
  const [isSaving, setIsSaving] = useState(false);

  const fetchGuestInfo = async (guestId: string) => {
    try {
      const response = await guestService.getGuestInfo(guestId);
      setGuestInfo(response);
      setOriginalGuestInfo(response);
    } catch (error) {}
  };

  useEffect(() => {
    if (open && guestId) {
      // Fetch guest information when the modal opens
      fetchGuestInfo(guestId);
      // Reset editable fields when modal opens
      setEditableFields({
        fullname: false,
        gender: false,
        birthday: false,
        email: false,
        phone: false,
        address: false,
        skinCondition: false,
      });
    }
  }, [open, guestId]);

  const toggleEditField = (fieldName: string) => {
    setEditableFields((prev) => ({
      ...prev,
      [fieldName]: !prev[fieldName],
    }));
  };

  const resetField = (fieldName: string) => {
    if (!originalGuestInfo || !guestInfo) return;

    setGuestInfo({
      ...guestInfo,
      [fieldName]: originalGuestInfo[fieldName as keyof GuestInfo],
    });
    toggleEditField(fieldName);
  };

  const handleInputChange = (fieldName: string, value: string) => {
    if (!guestInfo) return;

    setGuestInfo({
      ...guestInfo,
      [fieldName]: value,
    });
  };

  const handleSave = async () => {
    if (!guestInfo) return;
    setIsSaving(true);
    try {
      const updateData: GuestInfoUpdate = {
        fullname: guestInfo.fullname,
        email: guestInfo.email,
        phone: guestInfo.phone,
        address: guestInfo.address,
        gender: guestInfo.gender,
        birthday: guestInfo.birthday,
      };
      const updated = await guestService.updateGuestInfo(guestId, updateData);
      setGuestInfo(updated);
      setOriginalGuestInfo(updated);
      // Show success toast
      toast.success("Lưu thông tin thành công");
      // reset all editable fields
      setEditableFields(
        Object.keys(editableFields).reduce(
          (acc, key) => ({ ...acc, [key]: false }),
          {}
        )
      );
      onOpenChange(false);
    } catch (error) {
      console.error(error);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    guestInfo !== null && (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogTitle className="text-center text-lg font-bold"></DialogTitle>
        <DialogContent className="sm:max-w-[550px] p-0 overflow-hidden">
          <div className="flex flex-col items-center pt-8 pb-6 bg-white">
            <div className="relative">
              <Avatar className="h-24 w-24 border-2 border-[#6366F1]">
                <img
                  src={guestInfo.avatar}
                  alt="User avatar"
                  className="object-cover"
                />
              </Avatar>
              <div className="absolute bottom-0 right-0 h-5 w-5 rounded-full bg-[#0084FF] border-2 border-white"></div>
            </div>

            <h2 className="text-2xl font-bold mt-4">
              {guestInfo.account_name}
            </h2>
          </div>

          <div className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="w-[120px] font-medium">Tên:</div>
              <div className="flex-1 flex items-center">
                <Input
                  value={guestInfo.fullname}
                  className={`flex-1 ${
                    !editableFields.fullname ? "bg-gray-50" : "bg-white"
                  }`}
                  readOnly={!editableFields.fullname}
                  onChange={(e) =>
                    handleInputChange("fullname", e.target.value)
                  }
                />
                <Button
                  variant="ghost"
                  size="icon"
                  className="ml-2 h-8 w-8 text-gray-500"
                  onClick={() =>
                    editableFields.fullname
                      ? resetField("fullname")
                      : toggleEditField("fullname")
                  }
                >
                  {editableFields.fullname ? (
                    <RotateCcw className="h-4 w-4" />
                  ) : (
                    <Edit className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="w-[120px] font-medium">Giới tính:</div>
              <div className="flex-1 flex items-center">
                <Select
                  value={guestInfo.gender}
                  onValueChange={(value) => handleInputChange("gender", value)}
                >
                  <SelectTrigger
                    className={`flex-1 ${
                      !editableFields.gender ? "bg-gray-50" : "bg-white"
                    }`}
                    disabled={!editableFields.gender}
                  >
                    <SelectValue placeholder="Chọn giới tính" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="male">Nam</SelectItem>
                    <SelectItem value="female">Nữ</SelectItem>
                  </SelectContent>
                </Select>
                <Button
                  variant="ghost"
                  size="icon"
                  className="ml-2 h-8 w-8 text-gray-500"
                  onClick={() =>
                    editableFields.gender
                      ? resetField("gender")
                      : toggleEditField("gender")
                  }
                >
                  {editableFields.gender ? (
                    <RotateCcw className="h-4 w-4" />
                  ) : (
                    <Edit className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="w-[120px] font-medium">Năm sinh:</div>
              <div className="flex-1 flex items-center">
                {editableFields.birthday ? (
                  <Input
                    type="date"
                    value={guestInfo.birthday.slice(0, 10)}
                    className="flex-1 bg-white"
                    onChange={(e) =>
                      handleInputChange(
                        "birthday",
                        new Date(e.target.value).toISOString()
                      )
                    }
                  />
                ) : (
                  <Input
                    value={new Date(guestInfo.birthday).toLocaleDateString()}
                    readOnly
                    className="flex-1 bg-gray-50"
                  />
                )}
                <Button
                  variant="ghost"
                  size="icon"
                  className="ml-2 h-8 w-8 text-gray-500"
                  onClick={() =>
                    editableFields.birthday
                      ? resetField("birthday")
                      : toggleEditField("birthday")
                  }
                >
                  {editableFields.birthday ? (
                    <RotateCcw className="h-4 w-4" />
                  ) : (
                    <Edit className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="w-[120px] font-medium">Email:</div>
              <div className="flex-1 flex items-center">
                <Input
                  value={guestInfo?.email}
                  className={`flex-1 ${
                    !editableFields.email ? "bg-gray-50" : "bg-white"
                  }`}
                  readOnly={!editableFields.email}
                  onChange={(e) => handleInputChange("email", e.target.value)}
                />
                <Button
                  variant="ghost"
                  size="icon"
                  className="ml-2 h-8 w-8 text-gray-500"
                  onClick={() =>
                    editableFields.email
                      ? resetField("email")
                      : toggleEditField("email")
                  }
                >
                  {editableFields.email ? (
                    <RotateCcw className="h-4 w-4" />
                  ) : (
                    <Edit className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="w-[120px] font-medium">SĐT:</div>
              <div className="flex-1 flex items-center">
                <Input
                  value={guestInfo.phone}
                  className={`flex-1 ${
                    !editableFields.phone ? "bg-gray-50" : "bg-white"
                  }`}
                  readOnly={!editableFields.phone}
                  onChange={(e) => handleInputChange("phone", e.target.value)}
                />
                <Button
                  variant="ghost"
                  size="icon"
                  className="ml-2 h-8 w-8 text-gray-500"
                  onClick={() =>
                    editableFields.phone
                      ? resetField("phone")
                      : toggleEditField("phone")
                  }
                >
                  {editableFields.phone ? (
                    <RotateCcw className="h-4 w-4" />
                  ) : (
                    <Edit className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="w-[120px] font-medium">Địa chỉ:</div>
              <div className="flex-1 flex items-center">
                <Input
                  value={guestInfo.address}
                  className={`flex-1 ${
                    !editableFields.address ? "bg-gray-50" : "bg-white"
                  }`}
                  readOnly={!editableFields.address}
                  onChange={(e) => handleInputChange("address", e.target.value)}
                />
                <Button
                  variant="ghost"
                  size="icon"
                  className="ml-2 h-8 w-8 text-gray-500"
                  onClick={() =>
                    editableFields.address
                      ? resetField("address")
                      : toggleEditField("address")
                  }
                >
                  {editableFields.address ? (
                    <RotateCcw className="h-4 w-4" />
                  ) : (
                    <Edit className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="w-[120px] font-medium">Tình trạng da:</div>
              <div className="flex-1 flex items-center">
                <Textarea
                  value={guestInfo.skinCondition}
                  className={`flex-1 ${
                    !editableFields.skinCondition ? "bg-gray-50" : "bg-white"
                  }`}
                  readOnly={!editableFields.skinCondition}
                  onChange={(e) =>
                    handleInputChange("skinCondition", e.target.value)
                  }
                />
                <Button
                  variant="ghost"
                  size="icon"
                  className="ml-2 h-8 w-8 text-gray-500"
                  onClick={() =>
                    editableFields.skinCondition
                      ? resetField("skinCondition")
                      : toggleEditField("skinCondition")
                  }
                >
                  {editableFields.skinCondition ? (
                    <RotateCcw className="h-4 w-4" />
                  ) : (
                    <Edit className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
          </div>

          <div className="flex justify-center gap-4 p-6 pt-2">
            <Button
              variant="outline"
              className="w-24"
              onClick={() => onOpenChange(false)}
              disabled={isSaving}
            >
              Hủy
            </Button>
            <Button
              className="w-24 bg-[#6366F1] hover:bg-[#4F46E5]"
              onClick={handleSave}
              disabled={isSaving}
            >
              {isSaving ? "Đang lưu..." : "Lưu"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    )
  );
}
