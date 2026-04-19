import { useMemo, useState } from "react";
import { ArrowLeft, AlertTriangle, Trash2 } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { LanguageSelector } from "../components/LanguageSelector";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";

export default function DeleteAccountPage() {
  const navigate = useNavigate();
  const { user, deleteAccount, loading } = useAuth();
  const { isRtl } = useLanguage();
  const [confirmed, setConfirmed] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const email = useMemo(() => user?.email || "your account", [user]);

  const handleDelete = async () => {
    if (!confirmed || deleting) return;
    setDeleting(true);
    try {
      await deleteAccount();
      toast.success("Your account has been deleted.");
      navigate("/", { replace: true });
    } catch (error) {
      toast.error(error?.response?.data?.detail || "We couldn't delete your account right now.");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className={`min-h-screen bg-[#F8F9FA] ${isRtl ? "rtl" : "ltr"}`} data-testid="delete-account-page">
      <div className="ios-safe-header p-4 flex justify-between items-center">
        <Button variant="ghost" onClick={() => navigate(-1)} className="text-[#8D99AE]" data-testid="back-btn">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <LanguageSelector />
      </div>

      <main className="max-w-2xl mx-auto px-4 pb-16">
        <section className="bg-white rounded-2xl shadow-sm p-6 md:p-8 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-2xl bg-[#FF6B6B]/10 flex items-center justify-center">
              <Trash2 className="w-6 h-6 text-[#FF6B6B]" />
            </div>
            <div>
              <h1 className="text-3xl font-black text-[#2B2D42]" style={{ fontFamily: "Nunito, sans-serif" }}>
                Delete Account
              </h1>
              <p className="text-[#8D99AE] mt-1">Permanent deletion for your Caca Radar account</p>
            </div>
          </div>

          {!loading && !user ? (
            <div className="rounded-2xl border border-[#8D99AE]/20 bg-[#F8F9FA] p-5 space-y-3">
              <p className="text-[#5C677D] leading-7">
                Please sign in first if you want to delete your account from inside the app.
              </p>
              <div className="flex flex-wrap gap-3">
                <Link to="/login" className="inline-flex items-center rounded-xl bg-[#FF6B6B] px-4 py-2.5 text-white font-semibold">
                  Go to login
                </Link>
                <a href="mailto:jefe@cacaradar.es" className="inline-flex items-center rounded-xl border border-[#8D99AE]/20 px-4 py-2.5 text-[#2B2D42] font-semibold">
                  Email deletion request
                </a>
              </div>
            </div>
          ) : (
            <>
              <div className="rounded-2xl border border-[#FF6B6B]/20 bg-[#FFF5F5] p-5 space-y-4">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-[#FF6B6B] mt-0.5 flex-shrink-0" />
                  <div className="space-y-3 text-[#5C677D] leading-7">
                    <p>
                      You are about to permanently delete <span className="font-semibold text-[#2B2D42]">{email}</span>.
                    </p>
                    <p>
                      This removes your account, sign-in access, notifications, saved places, votes, and other user-specific records.
                    </p>
                    <p>
                      Reports you already published may remain in the service in anonymised form so the public map stays intact.
                    </p>
                  </div>
                </div>
              </div>

              <label className="mt-6 flex items-start gap-3 rounded-2xl border border-[#8D99AE]/20 bg-white p-4 cursor-pointer">
                <input
                  type="checkbox"
                  checked={confirmed}
                  onChange={(event) => setConfirmed(event.target.checked)}
                  className="mt-1 h-4 w-4 rounded border-[#8D99AE]"
                />
                <span className="text-sm text-[#2B2D42] leading-6">
                  I understand this action is permanent and I want to delete my account now.
                </span>
              </label>

              <div className="mt-6 flex flex-wrap gap-3">
                <Button
                  type="button"
                  onClick={handleDelete}
                  disabled={!confirmed || deleting}
                  className="bg-[#FF6B6B] hover:bg-[#FF5252] text-white rounded-xl px-5"
                  data-testid="confirm-delete-account"
                >
                  {deleting ? "Deleting..." : "Delete my account"}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => navigate("/profile")}
                  className="rounded-xl"
                >
                  Keep my account
                </Button>
              </div>
            </>
          )}
        </section>
      </main>
    </div>
  );
}
