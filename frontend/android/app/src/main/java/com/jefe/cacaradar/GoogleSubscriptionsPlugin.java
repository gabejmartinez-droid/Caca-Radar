package com.jefe.cacaradar;

import android.content.Intent;
import android.net.Uri;
import android.util.Log;

import com.android.billingclient.api.AcknowledgePurchaseParams;
import com.android.billingclient.api.BillingClient;
import com.android.billingclient.api.BillingClientStateListener;
import com.android.billingclient.api.BillingFlowParams;
import com.android.billingclient.api.BillingResult;
import com.android.billingclient.api.PendingPurchasesParams;
import com.android.billingclient.api.ProductDetails;
import com.android.billingclient.api.Purchase;
import com.android.billingclient.api.PurchasesUpdatedListener;
import com.android.billingclient.api.QueryProductDetailsParams;
import com.android.billingclient.api.QueryPurchasesParams;
import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

@CapacitorPlugin(name = "GoogleSubscriptions")
public class GoogleSubscriptionsPlugin extends Plugin implements PurchasesUpdatedListener {
    private static final String TAG = "GoogleSubscriptions";
    private BillingClient billingClient;
    private final Map<String, ProductDetails> productDetailsById = new HashMap<>();
    private PluginCall pendingPurchaseCall;

    private BillingClient getBillingClient() {
        if (billingClient == null) {
            PendingPurchasesParams pendingPurchasesParams = PendingPurchasesParams.newBuilder()
                .enableOneTimeProducts()
                .build();

            billingClient = BillingClient.newBuilder(getContext())
                .setListener(this)
                .enablePendingPurchases(pendingPurchasesParams)
                .build();
        }
        return billingClient;
    }

    private void withBillingClient(PluginCall call, Runnable runnable) {
        BillingClient client = getBillingClient();
        if (client.isReady()) {
            runnable.run();
            return;
        }

        client.startConnection(new BillingClientStateListener() {
            @Override
            public void onBillingSetupFinished(BillingResult billingResult) {
                if (billingResult.getResponseCode() == BillingClient.BillingResponseCode.OK) {
                    runnable.run();
                } else {
                    call.reject("Google Play Billing unavailable: " + billingResult.getDebugMessage());
                }
            }

            @Override
            public void onBillingServiceDisconnected() {
                Log.w(TAG, "Google Play Billing service disconnected");
            }
        });
    }

    @PluginMethod
    public void getProducts(PluginCall call) {
        JSArray productIds = call.getArray("productIds");
        if (productIds == null || productIds.length() == 0) {
            call.reject("Missing Google Play subscription identifiers");
            return;
        }

        ArrayList<QueryProductDetailsParams.Product> products = new ArrayList<>();
        for (int i = 0; i < productIds.length(); i++) {
            String productId = productIds.optString(i, "").trim();
            if (!productId.isEmpty()) {
                products.add(
                    QueryProductDetailsParams.Product.newBuilder()
                        .setProductId(productId)
                        .setProductType(BillingClient.ProductType.SUBS)
                        .build()
                );
            }
        }

        if (products.isEmpty()) {
            call.reject("Missing Google Play subscription identifiers");
            return;
        }

        withBillingClient(call, () -> getBillingClient().queryProductDetailsAsync(
            QueryProductDetailsParams.newBuilder().setProductList(products).build(),
            (billingResult, queryResult) -> {
                if (billingResult.getResponseCode() != BillingClient.BillingResponseCode.OK) {
                    call.reject("Failed to load Google Play products: " + billingResult.getDebugMessage());
                    return;
                }

                List<ProductDetails> productDetailsList = queryResult.getProductDetailsList();
                JSArray serializedProducts = new JSArray();
                for (ProductDetails details : productDetailsList) {
                    productDetailsById.put(details.getProductId(), details);
                    serializedProducts.put(serializeProduct(details));
                }

                JSObject result = new JSObject();
                result.put("products", serializedProducts);
                call.resolve(result);
            }
        ));
    }

    @PluginMethod
    public void purchase(PluginCall call) {
        String productId = call.getString("productId", "").trim();
        if (productId.isEmpty()) {
            call.reject("Missing Google Play subscription identifier");
            return;
        }

        withBillingClient(call, () -> {
            ProductDetails details = productDetailsById.get(productId);
            if (details == null) {
                call.reject("Google Play product not loaded: " + productId);
                return;
            }

            String offerToken = firstOfferToken(details);
            if (offerToken == null || offerToken.isEmpty()) {
                call.reject("Google Play product has no active subscription offer: " + productId);
                return;
            }

            if (pendingPurchaseCall != null) {
                call.reject("Another Google Play purchase is already in progress");
                return;
            }

            BillingFlowParams.ProductDetailsParams productDetailsParams =
                BillingFlowParams.ProductDetailsParams.newBuilder()
                    .setProductDetails(details)
                    .setOfferToken(offerToken)
                    .build();

            BillingFlowParams.Builder flowBuilder = BillingFlowParams.newBuilder()
                .setProductDetailsParamsList(singletonList(productDetailsParams));

            String obfuscatedAccountId = call.getString("obfuscatedAccountId", "").trim();
            if (!obfuscatedAccountId.isEmpty()) {
                flowBuilder.setObfuscatedAccountId(obfuscatedAccountId);
            }

            pendingPurchaseCall = call;
            BillingResult result = getBillingClient().launchBillingFlow(getActivity(), flowBuilder.build());
            if (result.getResponseCode() != BillingClient.BillingResponseCode.OK) {
                pendingPurchaseCall = null;
                call.reject("Failed to start Google Play purchase: " + result.getDebugMessage());
            }
        });
    }

    @PluginMethod
    public void restorePurchases(PluginCall call) {
        queryActivePurchases(call);
    }

    @PluginMethod
    public void getActiveSubscriptions(PluginCall call) {
        queryActivePurchases(call);
    }

    @PluginMethod
    public void acknowledgePurchase(PluginCall call) {
        String purchaseToken = call.getString("purchaseToken", "").trim();
        if (purchaseToken.isEmpty()) {
            call.reject("Missing Google Play purchase token");
            return;
        }

        withBillingClient(call, () -> {
            AcknowledgePurchaseParams params = AcknowledgePurchaseParams.newBuilder()
                .setPurchaseToken(purchaseToken)
                .build();

            getBillingClient().acknowledgePurchase(params, billingResult -> {
                if (billingResult.getResponseCode() == BillingClient.BillingResponseCode.OK
                    || billingResult.getResponseCode() == BillingClient.BillingResponseCode.ITEM_NOT_OWNED) {
                    call.resolve();
                    return;
                }
                call.reject("Failed to acknowledge Google Play purchase: " + billingResult.getDebugMessage());
            });
        });
    }

    @PluginMethod
    public void openSubscriptionManagement(PluginCall call) {
        String productId = call.getString("productId", "").trim();
        Uri.Builder uriBuilder = Uri.parse("https://play.google.com/store/account/subscriptions").buildUpon()
            .appendQueryParameter("package", getContext().getPackageName());
        if (!productId.isEmpty()) {
            uriBuilder.appendQueryParameter("sku", productId);
        }

        try {
            Intent intent = new Intent(Intent.ACTION_VIEW, uriBuilder.build());
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            getContext().startActivity(intent);
            call.resolve();
        } catch (Exception exception) {
            Log.e(TAG, "Unable to open Google Play subscription management", exception);
            call.reject("Unable to open Google Play subscription management", exception);
        }
    }

    @Override
    public void onPurchasesUpdated(BillingResult billingResult, List<Purchase> purchases) {
        PluginCall call = pendingPurchaseCall;
        pendingPurchaseCall = null;
        if (call == null) {
            return;
        }

        int responseCode = billingResult.getResponseCode();
        if (responseCode == BillingClient.BillingResponseCode.USER_CANCELED) {
            JSObject result = new JSObject();
            result.put("status", "cancelled");
            call.resolve(result);
            return;
        }
        if (responseCode != BillingClient.BillingResponseCode.OK) {
            call.reject("Google Play purchase failed: " + billingResult.getDebugMessage());
            return;
        }
        if (purchases == null || purchases.isEmpty()) {
            call.reject("Google Play purchase returned no purchase data");
            return;
        }

        Purchase purchase = purchases.get(0);
        JSObject result = serializePurchase(purchase);
        result.put("status", purchase.getPurchaseState() == Purchase.PurchaseState.PENDING ? "pending" : "purchased");
        call.resolve(result);
    }

    private void queryActivePurchases(PluginCall call) {
        withBillingClient(call, () -> getBillingClient().queryPurchasesAsync(
            QueryPurchasesParams.newBuilder()
                .setProductType(BillingClient.ProductType.SUBS)
                .build(),
            (billingResult, purchases) -> {
                if (billingResult.getResponseCode() != BillingClient.BillingResponseCode.OK) {
                    call.reject("Failed to query Google Play purchases: " + billingResult.getDebugMessage());
                    return;
                }

                JSArray subscriptions = new JSArray();
                for (Purchase purchase : purchases) {
                    subscriptions.put(serializePurchase(purchase));
                }

                JSObject result = new JSObject();
                result.put("status", purchases.isEmpty() ? "empty" : "restored");
                result.put("subscriptions", subscriptions);
                call.resolve(result);
            }
        ));
    }

    private JSObject serializeProduct(ProductDetails details) {
        JSObject result = new JSObject();
        result.put("id", details.getProductId());
        result.put("displayName", details.getName());
        result.put("description", details.getDescription());
        result.put("type", details.getProductType());

        ProductDetails.SubscriptionOfferDetails offer = firstOffer(details);
        if (offer != null && !offer.getPricingPhases().getPricingPhaseList().isEmpty()) {
            ProductDetails.PricingPhase pricingPhase = offer.getPricingPhases().getPricingPhaseList().get(0);
            result.put("displayPrice", pricingPhase.getFormattedPrice());
            result.put("billingPeriod", pricingPhase.getBillingPeriod());
            result.put("offerToken", offer.getOfferToken());
            result.put("hasIntroOffer", offer.getPricingPhases().getPricingPhaseList().size() > 1);
        }
        return result;
    }

    private JSObject serializePurchase(Purchase purchase) {
        JSObject result = new JSObject();
        result.put("purchaseToken", purchase.getPurchaseToken());
        result.put("orderId", purchase.getOrderId());
        result.put("packageName", purchase.getPackageName());
        result.put("purchaseTime", purchase.getPurchaseTime());
        result.put("isAcknowledged", purchase.isAcknowledged());
        result.put("isAutoRenewing", purchase.isAutoRenewing());

        JSArray products = new JSArray();
        for (String product : purchase.getProducts()) {
            products.put(product);
        }
        result.put("products", products);
        result.put("productId", purchase.getProducts().isEmpty() ? "" : purchase.getProducts().get(0));

        String state = "unknown";
        if (purchase.getPurchaseState() == Purchase.PurchaseState.PURCHASED) {
            state = "purchased";
        } else if (purchase.getPurchaseState() == Purchase.PurchaseState.PENDING) {
            state = "pending";
        } else if (purchase.getPurchaseState() == Purchase.PurchaseState.UNSPECIFIED_STATE) {
            state = "unspecified";
        }
        result.put("purchaseState", state);
        return result;
    }

    private ProductDetails.SubscriptionOfferDetails firstOffer(ProductDetails details) {
        List<ProductDetails.SubscriptionOfferDetails> offers = details.getSubscriptionOfferDetails();
        if (offers == null || offers.isEmpty()) {
            return null;
        }
        return offers.get(0);
    }

    private String firstOfferToken(ProductDetails details) {
        ProductDetails.SubscriptionOfferDetails offer = firstOffer(details);
        return offer == null ? null : offer.getOfferToken();
    }

    private <T> List<T> singletonList(T item) {
        ArrayList<T> list = new ArrayList<>();
        list.add(item);
        return list;
    }
}
