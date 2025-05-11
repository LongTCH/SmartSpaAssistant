"use client";

import { useEffect, useRef, useState } from "react";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";
import { guestService } from "@/services/api/guest.service";
import { interestService } from "@/services/api/interest.service";
import type { Conversation } from "@/types/conversation";
import type { GuestInfoUpdate } from "@/types/guest"; // Corrected import
import type { Interest } from "@/types/interest";

// Import new components
import { GuestInfoHeader } from "./modal-parts/GuestInfoHeader";
import { EditableInputRow } from "./modal-parts/EditableInputRow";
import { EditableGenderRow } from "./modal-parts/EditableGenderRow";
import { EditableBirthdayRow } from "./modal-parts/EditableBirthdayRow";
import { EditableInterestsRow } from "./modal-parts/EditableInterestsRow";
import { GuestInfoModalActions } from "./modal-parts/GuestInfoModalActions";

interface GuestInfoModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  guestId: string;
}

export function GuestInfoModal({
  open,
  onOpenChange,
  guestId,
}: GuestInfoModalProps) {
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
  const interestsContainerRef = useRef<HTMLDivElement | null>(null); // Adjusted to allow null
  const [isInterestsDropdownOpen, setIsInterestsDropdownOpen] = useState(false);

  const fetchGuestInfo = async (guestId: string) => {
    try {
      const response = await guestService.getGuestInfo(guestId);
      setGuestInfo(response);
      setOriginalGuestInfo(response);
      setSelectedInterestNames(
        response.interests?.map((interest) => interest.name) || []
      );
    } catch {
      setGuestInfo(null);
      setOriginalGuestInfo(null);
      setSelectedInterestNames([]);
      toast.error("Không thể tải thông tin khách hàng.");
    }
  };

  const fetchAllInterests = async () => {
    try {
      setIsInterestsLoading(true);
      const response = await interestService.getAllPublishedInterests();
      setAvailableInterests(response);
    } catch {
      toast.error("Không thể tải danh sách sở thích.");
    } finally {
      setIsInterestsLoading(false);
    }
  };

  useEffect(() => {
    if (open && guestId) {
      fetchGuestInfo(guestId);
      fetchAllInterests();
      setEditableFields({
        fullname: false,
        gender: false,
        birthday: false,
        email: false,
        phone: false,
        address: false,
        interests: false,
      });
      setIsInterestsDropdownOpen(false); // Close dropdown when modal reopens
    }
  }, [open, guestId]);

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

  const addInterest = (interestName: string) => {
    setSelectedInterestNames((prev) => [...prev, interestName]);
  };

  const removeInterest = (interestName: string) => {
    setSelectedInterestNames((prev) =>
      prev.filter((name) => name !== interestName)
    );
  };

  const toggleEditField = (fieldName: string) => {
    setEditableFields((prev) => ({
      ...prev,
      [fieldName]: !prev[fieldName],
    }));
    // If opening interests for edit, also open the dropdown
    if (fieldName === "interests" && !editableFields.interests) {
      setIsInterestsDropdownOpen(true);
    }
    // If closing interests edit, also close dropdown
    if (fieldName === "interests" && editableFields.interests) {
      setIsInterestsDropdownOpen(false);
    }
  };

  const resetField = (fieldName: keyof typeof editableFields) => {
    if (!originalGuestInfo || !guestInfo) return;
    const update: Partial<Conversation> = {};

    if (fieldName === "interests") {
      setSelectedInterestNames(
        originalGuestInfo.interests?.map((interest) => interest.name) || []
      );
      update.interests = originalGuestInfo.interests || [];
    } else if (fieldName === "gender") {
      update.gender = originalGuestInfo.gender;
    } else if (fieldName === "birthday") {
      update.birthday = originalGuestInfo.birthday;
    } else if (
      fieldName === "fullname" ||
      fieldName === "email" ||
      fieldName === "phone" ||
      fieldName === "address"
    ) {
      update[fieldName] = originalGuestInfo[fieldName];
    }

    setGuestInfo((prev) => ({
      ...prev!,
      ...update,
    }));
    toggleEditField(fieldName);
  };

  const handleInputChange = (
    fieldName: keyof Omit<typeof editableFields, "interests">, // Exclude interests as it's handled by add/remove
    value: string | null
  ) => {
    if (!guestInfo) return;
    let actualValueToStore: string | null;

    if (fieldName === "gender") {
      actualValueToStore = value === "unknown" ? null : value;
    } else {
      actualValueToStore = value === "" ? null : value;
    }

    setGuestInfo((prev) => ({
      ...prev!,
      [fieldName]: actualValueToStore,
    }));
  };

  const handleSave = async () => {
    if (!guestInfo) return;
    setIsSaving(true);
    try {
      const interestIds = selectedInterestNames
        .map((name) => {
          const interest = availableInterests.find((i) => i.name === name);
          return interest ? interest.id : null;
        })
        .filter((id): id is string => id !== null);

      const updateData: GuestInfoUpdate = {
        fullname: guestInfo.fullname || null,
        email: guestInfo.email || null,
        phone: guestInfo.phone || null,
        address: guestInfo.address || null,
        gender: guestInfo.gender,
        birthday: guestInfo.birthday
          ? new Date(guestInfo.birthday).toISOString()
          : null,
        interest_ids: interestIds,
      };

      const updatedGuestInfo = await guestService.updateGuestInfo(
        guestId,
        updateData
      );
      setGuestInfo(updatedGuestInfo);
      setOriginalGuestInfo(updatedGuestInfo);
      setSelectedInterestNames(
        updatedGuestInfo.interests?.map((i) => i.name) || []
      );

      toast.success("Lưu thông tin thành công");
      setEditableFields(
        Object.keys(editableFields).reduce(
          (acc, key) => ({ ...acc, [key]: false }),
          {}
        )
      );
      setIsInterestsDropdownOpen(false); // Close dropdown on save
      onOpenChange(false);
    } catch {
      toast.error("Không thể cập nhật thông tin");
    } finally {
      setIsSaving(false);
    }
  };

  const getSafeDateString = (
    isoDateString: string | null | undefined
  ): string => {
    if (!isoDateString) return "";
    try {
      return new Date(isoDateString).toISOString().slice(0, 10);
    } catch {
      return "";
    }
  };

  const formatSafeDate = (isoDateString: string | null | undefined): string => {
    if (!isoDateString) return "N/A";
    try {
      return new Date(isoDateString).toLocaleDateString("vi-VN");
    } catch {
      return "Invalid Date";
    }
  };

  return (
    guestInfo !== null && (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogTitle className="text-center text-lg font-bold"></DialogTitle>
        <DialogContent className="sm:max-w-[850px] h-full p-0 overflow-auto">
          <GuestInfoHeader
            avatarUrl={guestInfo.avatar}
            accountName={guestInfo.account_name}
          />

          <div className="p-6 space-y-4">
            <EditableInputRow
              label="Tên"
              value={guestInfo.fullname}
              placeholder="Chưa có thông tin"
              isEditable={editableFields.fullname}
              fieldName="fullname"
              onInputChange={handleInputChange}
              onToggleEdit={toggleEditField}
              onReset={resetField}
            />
            <EditableGenderRow
              label="Giới tính"
              value={guestInfo.gender}
              isEditable={editableFields.gender}
              fieldName="gender"
              onValueChange={handleInputChange}
              onToggleEdit={toggleEditField}
              onReset={resetField}
            />
            <EditableBirthdayRow
              label="Năm sinh"
              value={guestInfo.birthday}
              isEditable={editableFields.birthday}
              fieldName="birthday"
              onInputChange={handleInputChange}
              onToggleEdit={toggleEditField}
              onReset={resetField}
              getSafeDateString={getSafeDateString}
              formatSafeDate={formatSafeDate}
            />
            <EditableInputRow
              label="Email"
              value={guestInfo.email}
              placeholder="Chưa có thông tin"
              isEditable={editableFields.email}
              fieldName="email"
              onInputChange={handleInputChange}
              onToggleEdit={toggleEditField}
              onReset={resetField}
            />
            <EditableInputRow
              label="SĐT"
              value={guestInfo.phone}
              placeholder="Chưa có thông tin"
              isEditable={editableFields.phone}
              fieldName="phone"
              onInputChange={handleInputChange}
              onToggleEdit={toggleEditField}
              onReset={resetField}
            />
            <EditableInputRow
              label="Địa chỉ"
              value={guestInfo.address}
              placeholder="Chưa có thông tin"
              isEditable={editableFields.address}
              fieldName="address"
              onInputChange={handleInputChange}
              onToggleEdit={toggleEditField}
              onReset={resetField}
            />
            <EditableInterestsRow
              label="Sở thích"
              isEditable={editableFields.interests}
              fieldName="interests"
              onToggleEdit={toggleEditField}
              onReset={resetField}
              selectedInterestNames={selectedInterestNames}
              availableInterests={availableInterests}
              addInterest={addInterest}
              removeInterest={removeInterest}
              isInterestsLoading={isInterestsLoading}
              isInterestsDropdownOpen={isInterestsDropdownOpen}
              setIsInterestsDropdownOpen={setIsInterestsDropdownOpen}
              interestsContainerRef={interestsContainerRef}
            />
          </div>

          <GuestInfoModalActions
            onCancel={() => {
              if (originalGuestInfo) {
                setGuestInfo(originalGuestInfo);
                setSelectedInterestNames(
                  originalGuestInfo.interests?.map((i) => i.name) || []
                );
                setEditableFields(
                  Object.keys(editableFields).reduce(
                    (acc, key) => ({ ...acc, [key]: false }),
                    {}
                  )
                );
              }
              setIsInterestsDropdownOpen(false); // Close dropdown on cancel
              onOpenChange(false);
            }}
            onSave={handleSave}
            isSaving={isSaving}
            canSave={Object.values(editableFields).some(Boolean)}
          />
        </DialogContent>
      </Dialog>
    )
  );
}
