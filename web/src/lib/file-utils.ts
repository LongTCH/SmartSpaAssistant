/**
 * Utility function to download a file from a blob or URL
 *
 * @param blobOrUrl The blob data or URL to download
 * @param fileName The name to give to the downloaded file
 * @returns Promise that resolves once download is initiated
 */
export function downloadFile(
  blobOrUrl: Blob | string,
  fileName: string
): Promise<void> {
  return new Promise((resolve, reject) => {
    try {
      // Create URL from blob if needed
      const url =
        blobOrUrl instanceof Blob
          ? window.URL.createObjectURL(blobOrUrl)
          : blobOrUrl;

      // Create a temporary link element
      const link = document.createElement("a");
      link.href = url;
      link.download = fileName;

      // Append to the document, trigger the download
      document.body.appendChild(link);
      link.click();

      // Clean up
      window.setTimeout(() => {
        document.body.removeChild(link);
        // Only revoke if we created the URL
        if (blobOrUrl instanceof Blob) {
          window.URL.revokeObjectURL(url);
        }
        resolve();
      }, 100);
    } catch (error) {
      reject(error);
    }
  });
}
