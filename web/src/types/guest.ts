import { Interest } from "./interest";

export interface GuestInfo {
  id: string;
  account_name: string;
  fullname: string;
  email: string;
  phone: string;
  avatar: string;
  address: string;
  gender: string;
  birthday: string;
  interests: Interest[];
}

export interface GuestInfoUpdate {
  fullname: string;
  email: string;
  phone: string;
  address: string;
  gender: string;
  birthday: string;
}
