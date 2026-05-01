import { Facebook, Instagram, MessageCircle } from "lucide-react";
import { Button } from "./ui/button";
import { openFacebookShare, openWhatsAppShare, shareToInstagram, shareWithNativeOrCopy } from "../utils/socialShare";

function SocialShareButtons({ loadShareData, onError, onCopied, className = "", prefix = "social-share" }) {
  const runShare = async (action) => {
    try {
      const shareData = await loadShareData();
      if (!shareData?.url) throw new Error("missing_share_url");
      await action(shareData);
    } catch (error) {
      if (error?.name !== "AbortError" && onError) onError(error);
    }
  };

  return (
    <div className={`grid gap-2 [grid-template-columns:repeat(auto-fit,minmax(140px,1fr))] ${className}`}>
      <Button
        type="button"
        variant="outline"
        className="min-w-0 h-auto rounded-xl border-[#1877F2]/25 px-3 py-3 text-sm font-semibold leading-tight text-[#1877F2] hover:bg-[#1877F2]/10 whitespace-normal"
        onClick={() => runShare((shareData) => openFacebookShare(shareData.url))}
        data-testid={`${prefix}-facebook`}
      >
        <span className="flex min-w-0 items-center justify-center gap-2 text-center">
          <Facebook className="h-4 w-4 shrink-0" />
          <span className="min-w-0 break-words">Facebook</span>
        </span>
      </Button>
      <Button
        type="button"
        variant="outline"
        className="min-w-0 h-auto rounded-xl border-[#E4405F]/25 px-3 py-3 text-sm font-semibold leading-tight text-[#E4405F] hover:bg-[#E4405F]/10 whitespace-normal"
        onClick={() => runShare((shareData) => shareToInstagram({ ...shareData, onCopied }))}
        data-testid={`${prefix}-instagram`}
      >
        <span className="flex min-w-0 items-center justify-center gap-2 text-center">
          <Instagram className="h-4 w-4 shrink-0" />
          <span className="min-w-0 break-words">Instagram</span>
        </span>
      </Button>
      <Button
        type="button"
        variant="outline"
        className="min-w-0 h-auto rounded-xl border-[#25D366]/25 px-3 py-3 text-sm font-semibold leading-tight text-[#25D366] hover:bg-[#25D366]/10 whitespace-normal"
        onClick={() => runShare((shareData) => {
          if (navigator.share) {
            return shareWithNativeOrCopy({ ...shareData, onCopied, allowFiles: false });
          }
          return openWhatsAppShare(shareData.text, shareData.url);
        })}
        data-testid={`${prefix}-whatsapp`}
      >
        <span className="flex min-w-0 items-center justify-center gap-2 text-center">
          <MessageCircle className="h-4 w-4 shrink-0" />
          <span className="min-w-0 break-words">WhatsApp</span>
        </span>
      </Button>
    </div>
  );
}

export default SocialShareButtons;
