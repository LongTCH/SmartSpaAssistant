/**
 * Lấy formatter định dạng ngày từ locale của trình duyệt
 * @returns Intl.DateTimeFormat cho ngày tháng (không có giờ)
 */
export function getDateFormatter(): Intl.DateTimeFormat {
  const userLocale = navigator.language || "vi-VN";
  return new Intl.DateTimeFormat(userLocale, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

/**
 * Lấy formatter định dạng ngày giờ từ locale của trình duyệt
 * @returns Intl.DateTimeFormat cho ngày tháng kèm giờ phút
 */
export function getDateTimeFormatter(): Intl.DateTimeFormat {
  const userLocale = navigator.language || "vi-VN";
  return new Intl.DateTimeFormat(userLocale, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Chuyển đổi thời gian UTC từ server sang timezone hiện tại của client
 * @param utcTimeString Chuỗi thời gian UTC từ server
 * @returns Date object với timezone hiện tại
 */
export function convertUTCToLocal(utcTimeString: string): Date {
  // Đảm bảo có 'Z' ở cuối để đánh dấu là UTC
  const utcString = utcTimeString.includes("Z")
    ? utcTimeString
    : utcTimeString + "Z";
  return new Date(utcString);
}

/**
 * Định dạng giá trị Date hoặc giá trị có thể chuyển thành Date
 * @param value Giá trị cần định dạng (UTC time string hoặc Date)
 * @param includeTime Có hiển thị giờ phút hay không
 * @returns Chuỗi ngày tháng đã định dạng theo locale người dùng
 */
export function formatDate(
  value: Date | string | number,
  includeTime = false
): string {
  try {
    let date: Date;

    if (value instanceof Date) {
      date = value;
    } else if (typeof value === "string") {
      // Nếu là string, coi như UTC time từ server
      date = convertUTCToLocal(value);
    } else {
      date = new Date(value);
    }

    if (isNaN(date.getTime())) {
      return String(value);
    }

    const formatter =
      includeTime || date.getHours() > 0 || date.getMinutes() > 0
        ? getDateTimeFormatter()
        : getDateFormatter();

    return formatter.format(date);
  } catch {
    return String(value);
  }
}
