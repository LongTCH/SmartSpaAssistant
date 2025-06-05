"use client";

import { useEffect, useRef, useState } from "react";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";
import { guestService } from "@/services/api/guest.service";
import { interestService } from "@/services/api/interest.service";
import type { Conversation as BaseConversation } from "@/types/conversation"; // Renamed import
import type { GuestInfo, GuestInfoUpdate } from "@/types/guest";
import type { Interest } from "@/types/interest";

// Import new components
import { GuestInfoHeader } from "./modal-parts/GuestInfoHeader";
import { EditableInputRow } from "./modal-parts/EditableInputRow";
import { EditableGenderRow } from "./modal-parts/EditableGenderRow";
import { EditableBirthdayRow } from "./modal-parts/EditableBirthdayRow";
import { EditableInterestsRow } from "./modal-parts/EditableInterestsRow";
import { GuestInfoModalActions } from "./modal-parts/GuestInfoModalActions";

// Define defaultGuestInfo outside the component or at the top of the file
const defaultGuestInfo: GuestInfo = {
  fullname: null,
  email: null,
  phone: null,
  address: null,
  gender: null,
  birthday: null,
};

// Define the new type where 'info' is mandatory
interface LoadedConversation extends Omit<BaseConversation, "info"> {
  info: GuestInfo;
}

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
  const [guestInfo, setGuestInfo] = useState<LoadedConversation | null>(null); // Updated type
  const [originalGuestInfo, setOriginalGuestInfo] =
    useState<LoadedConversation | null>(null); // Updated type
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
  const [availableInterests, setAvailableInterests] = useState<Interest[]>([]);
  const [selectedInterestNames, setSelectedInterestNames] = useState<string[]>(
    []
  );
  const [isInterestsLoading, setIsInterestsLoading] = useState(false);
  const [isInterestsDropdownOpen, setIsInterestsDropdownOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const interestsContainerRef = useRef<HTMLDivElement | null>(null);
  const loadingInterestsRef = useRef(false); // Prevent concurrent interests API calls

  const fetchGuestInfo = async (guestId: string) => {
    try {
      const response = await guestService.getGuestInfo(guestId); // response is BaseConversation
      // Ensure the data conforms to LoadedConversation
      const loadedData: LoadedConversation = {
        ...response,
        info: response.info ?? defaultGuestInfo,
      };
      setGuestInfo(loadedData);
      setOriginalGuestInfo(loadedData);
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
    // Prevent concurrent API calls
    if (loadingInterestsRef.current) return;

    try {
      loadingInterestsRef.current = true;
      setIsInterestsLoading(true);
      const response = await interestService.getAllPublishedInterests();
      setAvailableInterests(response);
    } catch {
      toast.error("Không thể tải danh sách sở thích.");
    } finally {
      setIsInterestsLoading(false);
      loadingInterestsRef.current = false;
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
    if (!originalGuestInfo || !guestInfo) return; // They are LoadedConversation | null here

    setGuestInfo((prev) => {
      // prev is LoadedConversation | null
      if (!prev) return prev; // Should be caught by the outer check

      // prev is LoadedConversation, so prev.info is guaranteed.
      // originalGuestInfo is also LoadedConversation, so originalGuestInfo.info is guaranteed.
      const newInfo = { ...prev.info }; // Create a copy of the info object
      let newInterests = prev.interests;

      if (fieldName === "interests") {
        setSelectedInterestNames(
          originalGuestInfo.interests?.map((interest) => interest.name) || []
        );
        newInterests = originalGuestInfo.interests || [];
      } else {
        // fieldName is a key of GuestInfo here
        // originalGuestInfo.info is guaranteed to exist.
        if (fieldName === "gender") {
          newInfo.gender = originalGuestInfo.info.gender;
        } else if (fieldName === "birthday") {
          newInfo.birthday = originalGuestInfo.info.birthday;
        } else if (
          fieldName === "fullname" ||
          fieldName === "email" ||
          fieldName === "phone" ||
          fieldName === "address"
        ) {
          newInfo[fieldName as keyof GuestInfo] =
            originalGuestInfo.info[fieldName as keyof GuestInfo];
        }
      }

      return {
        ...prev,
        info: newInfo,
        interests: newInterests,
      };
    });
    toggleEditField(fieldName);
  };

  const handleInputChange = (
    fieldName: keyof Omit<typeof editableFields, "interests">, // This resolves to keys of GuestInfo
    value: string | null
  ) => {
    setGuestInfo((prev) => {
      // prev is LoadedConversation | null
      if (!prev) return prev; // If prev is null, return null. prev.info is guaranteed if prev is not null.

      let actualValueToStore: string | null;
      if (fieldName === "gender") {
        actualValueToStore = value === "unknown" ? null : value;
      } else {
        actualValueToStore = value === "" ? null : value;
      }

      // Create a new info object with the updated field
      const newInfo = {
        ...prev.info,
        [fieldName]: actualValueToStore,
      };
      return { ...prev, info: newInfo };
    });
  };

  const handleSave = async () => {
    if (!guestInfo) return; // guestInfo is LoadedConversation, so guestInfo.info is guaranteed.
    setIsSaving(true);
    try {
      const interestIds = selectedInterestNames
        .map((name) => {
          const interest = availableInterests.find((i) => i.name === name);
          return interest ? interest.id : null;
        })
        .filter((id): id is string => id !== null);

      const currentInfo = guestInfo.info; // This is now safe

      const updateData: GuestInfoUpdate = {
        fullname: currentInfo.fullname,
        email: currentInfo.email,
        phone: currentInfo.phone,
        address: currentInfo.address,
        gender: currentInfo.gender,
        birthday: currentInfo.birthday
          ? new Date(currentInfo.birthday).toISOString()
          : null,
        interest_ids: interestIds,
      };

      const updatedConversationResponse = await guestService.updateGuestInfo(
        // Returns BaseConversation
        guestId,
        updateData
      );
      // Ensure the updated data also conforms to LoadedConversation
      const ensuredUpdatedConversation: LoadedConversation = {
        ...updatedConversationResponse,
        info: updatedConversationResponse.info ?? defaultGuestInfo,
      };

      setGuestInfo(ensuredUpdatedConversation);
      setOriginalGuestInfo(ensuredUpdatedConversation);
      setSelectedInterestNames(
        ensuredUpdatedConversation.interests?.map((i) => i.name) || []
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
      const date = new Date(isoDateString);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, "0");
      const day = String(date.getDate()).padStart(2, "0");
      return `${year}-${month}-${day}`;
    } catch {
      return "";
    }
  };

  const formatSafeDate = (isoDateString: string | null | undefined): string => {
    if (!isoDateString) return "N/A";
    try {
      return new Date(isoDateString).toLocaleDateString();
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
              value={guestInfo.info.fullname} // Safe: guestInfo.info is GuestInfo
              placeholder="Chưa có thông tin"
              isEditable={editableFields.fullname}
              fieldName="fullname"
              onInputChange={handleInputChange}
              onToggleEdit={toggleEditField}
              onReset={resetField}
            />
            <EditableGenderRow
              label="Giới tính"
              value={guestInfo.info.gender} // Safe
              isEditable={editableFields.gender}
              fieldName="gender"
              onValueChange={handleInputChange}
              onToggleEdit={toggleEditField}
              onReset={resetField}
            />
            <EditableBirthdayRow
              label="Năm sinh"
              value={guestInfo.info.birthday} // Safe
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
              value={guestInfo.info.email} // Safe
              placeholder="Chưa có thông tin"
              isEditable={editableFields.email}
              fieldName="email"
              onInputChange={handleInputChange}
              onToggleEdit={toggleEditField}
              onReset={resetField}
            />
            <EditableInputRow
              label="SĐT"
              value={guestInfo.info.phone} // Safe
              placeholder="Chưa có thông tin"
              isEditable={editableFields.phone}
              fieldName="phone"
              onInputChange={handleInputChange}
              onToggleEdit={toggleEditField}
              onReset={resetField}
            />
            <EditableInputRow
              label="Địa chỉ"
              value={guestInfo.info.address} // Safe
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
