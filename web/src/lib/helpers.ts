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
 * Định dạng giá trị Date hoặc giá trị có thể chuyển thành Date
 * @param value Giá trị cần định dạng
 * @param includeTime Có hiển thị giờ phút hay không
 * @returns Chuỗi ngày tháng đã định dạng theo locale người dùng
 */
export function formatDate(
  value: Date | string | number,
  includeTime = false
): string {
  try {
    const date = value instanceof Date ? value : new Date(value);

    if (isNaN(date.getTime())) {
      return String(value);
    }

    const formatter =
      includeTime || date.getHours() > 0 || date.getMinutes() > 0
        ? getDateTimeFormatter()
        : getDateFormatter();

    return formatter.format(date);
  } catch (e) {
    return String(value);
  }
}
