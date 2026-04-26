async function fetchShareFile(imageUrl) {
  const response = await fetch(imageUrl, { credentials: "include" });
  if (!response.ok) throw new Error("share_image_fetch_failed");
  const blob = await response.blob();
  const type = blob.type || "image/svg+xml";
  const extension = type.includes("svg") ? "svg" : "png";
  return new File([blob], `caca-radar-share.${extension}`, {
    type,
    lastModified: Date.now(),
  });
}

export async function shareWithNativeOrCopy({ title, text, url, imageUrl, onCopied, allowFiles = true }) {
  if (navigator.share) {
    if (allowFiles && imageUrl && navigator.canShare) {
      try {
        const file = await fetchShareFile(imageUrl);
        if (navigator.canShare({ files: [file] })) {
          await navigator.share({ title, text, url, files: [file] });
          return;
        }
      } catch {
        // fall back to text/url sharing below
      }
    }

    await navigator.share({ title, text, url });
    return;
  }

  await navigator.clipboard.writeText([text, url].filter(Boolean).join("\n\n"));
  if (onCopied) onCopied();
}

export function openFacebookShare(url) {
  window.open(
    `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`,
    "_blank",
    "noopener,noreferrer"
  );
}

export function openWhatsAppShare(text, url) {
  const shareText = [text, url].filter(Boolean).join(" ");
  window.open(
    `https://wa.me/?text=${encodeURIComponent(shareText)}`,
    "_blank",
    "noopener,noreferrer"
  );
}

export async function shareToInstagram({ title, text, url, onCopied }) {
  await shareWithNativeOrCopy({ title, text, url, onCopied, allowFiles: false });
}
