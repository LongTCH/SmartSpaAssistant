import { Interest } from "./interest";

export interface GuestInfoUpdate {
  fullname: string | null;
  email: string | null;
  phone: string | null;
  address: string | null;
  gender: string | null;
  birthday: string | null;
  interest_ids: string[];
}
