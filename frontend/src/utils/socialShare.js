export async function shareWithNativeOrCopy({ title, text, url, onCopied }) {
  if (navigator.share) {
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
  if (navigator.share) {
    await navigator.share({ title, text, url });
    return;
  }

  await navigator.clipboard.writeText([text, url].filter(Boolean).join("\n\n"));
  if (onCopied) onCopied();
}
