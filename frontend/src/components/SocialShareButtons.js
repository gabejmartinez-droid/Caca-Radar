import { Facebook, Instagram, MessageCircle } from "lucide-react";
import { Button } from "./ui/button";
import { openFacebookShare, openWhatsAppShare, shareToInstagram } from "../utils/socialShare";

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
    <div className={`grid grid-cols-3 gap-2 ${className}`}>
      <Button
        type="button"
        variant="outline"
        className="rounded-xl border-[#1877F2]/25 text-[#1877F2] hover:bg-[#1877F2]/10"
        onClick={() => runShare(({ url }) => openFacebookShare(url))}
        data-testid={`${prefix}-facebook`}
      >
        <Facebook className="w-4 h-4 mr-1.5" />
        Facebook
      </Button>
      <Button
        type="button"
        variant="outline"
        className="rounded-xl border-[#E4405F]/25 text-[#E4405F] hover:bg-[#E4405F]/10"
        onClick={() => runShare((shareData) => shareToInstagram({ ...shareData, onCopied }))}
        data-testid={`${prefix}-instagram`}
      >
        <Instagram className="w-4 h-4 mr-1.5" />
        Instagram
      </Button>
      <Button
        type="button"
        variant="outline"
        className="rounded-xl border-[#25D366]/25 text-[#25D366] hover:bg-[#25D366]/10"
        onClick={() => runShare(({ text, url }) => openWhatsAppShare(text, url))}
        data-testid={`${prefix}-whatsapp`}
      >
        <MessageCircle className="w-4 h-4 mr-1.5" />
        WhatsApp
      </Button>
    </div>
  );
}

export default SocialShareButtons;
