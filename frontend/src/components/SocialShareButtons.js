import { Share2 } from "lucide-react";
import { Button } from "./ui/button";
import { shareWithNativeOrCopy } from "../utils/socialShare";

function SocialShareButtons({ loadShareData, onError, onCopied, className = "", prefix = "social-share", label = "Share" }) {
  const runShare = async () => {
    try {
      const shareData = await loadShareData();
      if (!shareData?.url) throw new Error("missing_share_url");
      await shareWithNativeOrCopy({ ...shareData, onCopied, allowFiles: true });
    } catch (error) {
      if (error?.name !== "AbortError" && onError) onError(error);
    }
  };

  return (
    <div className={className}>
      <Button
        type="button"
        variant="outline"
        className="w-full min-w-0 h-auto rounded-xl border-[#FF6B6B]/30 px-4 py-3 text-sm font-semibold leading-tight text-[#FF6B6B] hover:bg-[#FF6B6B]/10 whitespace-normal"
        onClick={runShare}
        data-testid={`${prefix}-button`}
      >
        <span className="flex min-w-0 items-center justify-center gap-2 text-center">
          <Share2 className="h-4 w-4 shrink-0" />
          <span className="min-w-0 break-words">{label}</span>
        </span>
      </Button>
    </div>
  );
}

export default SocialShareButtons;
