export interface GuestInfo {
  fullname: string | null;
  email: string | null;
  phone: string | null;
  address: string | null;
  gender: string | null;
  birthday: string | null;
}

export interface GuestInfoUpdate {
  fullname: string | null;
  email: string | null;
  phone: string | null;
  address: string | null;
  gender: string | null;
  birthday: string | null;
  interest_ids: string[];
}
