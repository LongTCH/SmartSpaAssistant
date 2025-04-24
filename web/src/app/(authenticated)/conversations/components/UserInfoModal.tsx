"use client";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Conversation, GuestInfoUpdate, Interest } from "@/types";
import { Edit, RotateCcw, X } from "lucide-react";
import { useEffect, useState, useRef } from "react";
import { guestService } from "@/services/api/guest.service";
import { interestService } from "@/services/api/interest.service";
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
  const [guestInfo, setGuestInfo] = useState<Conversation | null>(null);
  const [originalGuestInfo, setOriginalGuestInfo] =
    useState<Conversation | null>(null);
  const [editableFields, setEditableFields] = useState<Record<string, boolean>>(
    {
      fullname: false,
      gender: false,
      birthday: false,
      email: false,
      phone: false,
      address: false,
      interests: false,
    }
  );
  const [isSaving, setIsSaving] = useState(false);
  const [availableInterests, setAvailableInterests] = useState<Interest[]>([]);
  const [selectedInterestNames, setSelectedInterestNames] = useState<string[]>(
    []
  );
  const [isInterestsLoading, setIsInterestsLoading] = useState(false);
  const interestsContainerRef = useRef<HTMLDivElement>(null);
  const [isInterestsDropdownOpen, setIsInterestsDropdownOpen] = useState(false);

  const fetchGuestInfo = async (guestId: string) => {
    try {
      const response = await guestService.getGuestInfo(guestId);
      setGuestInfo(response);
      setOriginalGuestInfo(response);
      // Khởi tạo danh sách tên nhãn đã chọn từ danh sách interests
      setSelectedInterestNames(
        response.interests.map((interest) => interest.name)
      );
    } catch (error) {
      console.error("Error fetching guest info:", error);
    }
  };

  // Fetch tất cả nhãn từ API
  const fetchAllInterests = async () => {
    try {
      setIsInterestsLoading(true);
      const response = await interestService.getAllPublishedInterests();
      setAvailableInterests(response);
    } catch (error) {
      console.error("Error fetching interests:", error);
    } finally {
      setIsInterestsLoading(false);
    }
  };

  useEffect(() => {
    if (open && guestId) {
      // Fetch guest information when the modal opens
      fetchGuestInfo(guestId);
      // Fetch all interests when modal opens
      fetchAllInterests();
      // Reset editable fields when modal opens
      setEditableFields({
        fullname: false,
        gender: false,
        birthday: false,
        email: false,
        phone: false,
        address: false,
        interests: false,
      });
    }
  }, [open, guestId]);

  // Đóng dropdown khi click ra ngoài
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        interestsContainerRef.current &&
        !interestsContainerRef.current.contains(event.target as Node)
      ) {
        setIsInterestsDropdownOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  // Add a keyword to selected list
  const addInterest = (interestName: string) => {
    setSelectedInterestNames((prev) => [...prev, interestName]);
  };

  // Remove a keyword from selected list
  const removeInterest = (interestName: string) => {
    setSelectedInterestNames((prev) =>
      prev.filter((name) => name !== interestName)
    );
  };

  // Find interest object by name
  const getInterestByName = (name: string): Interest | undefined => {
    return availableInterests.find((interest) => interest.name === name);
  };

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
      [fieldName]: originalGuestInfo[fieldName as keyof Conversation],
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
      // Lấy danh sách ID của các nhãn đã chọn
      const interestIds = selectedInterestNames
        .map((name) => {
          const interest = availableInterests.find((i) => i.name === name);
          return interest ? interest.id : null;
        })
        .filter((id): id is string => id !== null);

      const updateData: GuestInfoUpdate = {
        fullname: guestInfo.fullname,
        email: guestInfo.email,
        phone: guestInfo.phone,
        address: guestInfo.address,
        gender: guestInfo.gender,
        birthday: guestInfo.birthday,
        interest_ids: interestIds,
      };

      const updatedGuestInfo = await guestService.updateGuestInfo(
        guestId,
        updateData
      );
      setGuestInfo(updatedGuestInfo);
      setOriginalGuestInfo(updatedGuestInfo);
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
      toast.error("Không thể cập nhật thông tin");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    guestInfo !== null && (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogTitle className="text-center text-lg font-bold"></DialogTitle>
        <DialogContent className="sm:max-w-[850px] p-0 overflow-hidden">
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
              <div className="w-[120px] font-medium">Nhãn:</div>
              <div className="flex-1 flex items-center">
                <div className="flex-1 relative" ref={interestsContainerRef}>
                  <div
                    className={`flex flex-wrap min-h-10 max-h-24 overflow-y-auto px-3 py-2 border rounded-md ${
                      isInterestsDropdownOpen
                        ? "border-[#6366F1] ring-2 ring-[#6366F1]/20"
                        : "border-input"
                    } ${
                      !editableFields.interests ? "bg-gray-50" : "bg-white"
                    } gap-1 cursor-pointer`}
                    onClick={() => {
                      if (editableFields.interests) {
                        setIsInterestsDropdownOpen(true);
                      }
                    }}
                  >
                    {selectedInterestNames.length > 0 ? (
                      selectedInterestNames.map((interestName) => {
                        const interest = getInterestByName(interestName);
                        const color = interest?.color || "#6366F1";

                        return (
                          <Badge
                            key={interestName}
                            className="mb-1 inline-flex"
                            style={{
                              backgroundColor: `${color}20`, // 20% opacity
                              color: color,
                              borderColor: `${color}30`, // 30% opacity
                            }}
                          >
                            {interestName}
                            {editableFields.interests && (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-4 w-4 p-0 ml-1 hover:bg-transparent"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  removeInterest(interestName);
                                }}
                              >
                                <X className="h-3 w-3" />
                              </Button>
                            )}
                          </Badge>
                        );
                      })
                    ) : (
                      <span className="text-muted-foreground text-sm">
                        Chọn nhãn...
                      </span>
                    )}
                  </div>

                  {isInterestsDropdownOpen && editableFields.interests && (
                    <div className="absolute z-50 w-full mt-1 bg-white border rounded-md shadow-lg max-h-60 overflow-auto">
                      {isInterestsLoading ? (
                        <div className="px-3 py-2 text-center">Đang tải...</div>
                      ) : availableInterests.filter(
                          (interest) =>
                            !selectedInterestNames.includes(interest.name)
                        ).length > 0 ? (
                        availableInterests
                          .filter(
                            (interest) =>
                              !selectedInterestNames.includes(interest.name)
                          )
                          .map((interest) => (
                            <div
                              key={interest.id}
                              className="px-3 py-2 hover:bg-slate-100 cursor-pointer flex items-center"
                              onClick={() => {
                                addInterest(interest.name);
                                if (
                                  availableInterests.filter(
                                    (i) =>
                                      !selectedInterestNames.includes(i.name)
                                  ).length === 1
                                ) {
                                  setIsInterestsDropdownOpen(false);
                                }
                              }}
                            >
                              <div
                                className="w-3 h-3 rounded-full mr-2"
                                style={{ backgroundColor: interest.color }}
                              />
                              {interest.name}
                            </div>
                          ))
                      ) : (
                        <div className="px-3 py-2 text-center text-gray-500">
                          Không có nhãn nào
                        </div>
                      )}
                    </div>
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="ml-2 h-8 w-8 text-gray-500"
                  onClick={() =>
                    editableFields.interests
                      ? (() => {
                          // Nếu đang trong chế độ sửa, reset về danh sách nhãn ban đầu
                          if (originalGuestInfo) {
                            setSelectedInterestNames(
                              originalGuestInfo.interests.map(
                                (interest) => interest.name
                              )
                            );
                          }
                          toggleEditField("interests");
                          setIsInterestsDropdownOpen(false);
                        })()
                      : toggleEditField("interests")
                  }
                >
                  {editableFields.interests ? (
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
