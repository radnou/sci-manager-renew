<script lang="ts">
    import { onMount } from "svelte";
    import { goto } from "$app/navigation";
    import { getCurrentSession } from "$lib/auth/session";
    import { Button } from "$lib/components/ui/button";
    import { Badge } from "$lib/components/ui/badge";
    import { Card, CardContent, CardHeader, CardTitle } from "$lib/components/ui/card";
    import { Building2, FileText, TrendingUp, Shield, Users, Calculator, Check, ArrowRight, Briefcase, BarChart3, ChevronDown, ChevronUp, Loader2, Crown } from "lucide-svelte";
    import { API_URL } from "$lib/api";
    import { supabase } from "$lib/supabase";
    import CheckoutConfirmModal from "$lib/components/CheckoutConfirmModal.svelte";
    import AppDemoVideo from "$lib/components/AppDemoVideo.svelte";
    import { trackEvent, EVENTS } from "$lib/analytics";
    import { PLANS_LIST, formatPrice, formatPeriod, formatPriceTTC } from "$lib/config/plans";

    // Composants landing
    import HeroSection from "$lib/landing/HeroSection.svelte";
    import FeaturesSection from "$lib/landing/FeaturesSection.svelte";
    import CommentCaMarcheSection from "$lib/landing/CommentCaMarcheSection.svelte";
    import TargetAudienceSection from "$lib/landing/TargetAudienceSection.svelte";
    import ValueStackSection from "$lib/landing/ValueStackSection.svelte";
    import PricingSection from "$lib/landing/PricingSection.svelte";
    import GuaranteeSection from "$lib/landing/GuaranteeSection.svelte";
    import CTASection from "$lib/landing/CTASection.svelte";
    import FAQSection from "$lib/landing/FAQSection.svelte";
    import TrustBar from "$lib/landing/TrustBar.svelte";
    import CookieBanner from "$lib/components/CookieBanner.svelte";

    onMount(async () => {
        const session = await getCurrentSession();
        if (session?.user) {
            goto("/dashboard");
        }
    });

    let billingPeriod = $state<'month' | 'year'>('month');
    let checkoutLoading = $state<string | null>(null);
    let modalOpen = $state(false);
    let modalPlanKey = $state('');
    let modalPlanName = $state('');
    let modalPlanPrice = $state('');
    let modalPlanPeriod = $state('');
    let modalPlanFeatures = $state<string[]>([]);
    let openFaqIndex = $state<number | null>(null);
    let demoScene = $state(0);
    let lightboxOpen = $state(false);
    let lightboxIndex = $state(0);

    const allImages = [
        { src: "/images/showcase/dashboard-light.png", title: "Tableau de bord" },
        { src: "/images/showcase/biens-grid.png", title: "Grille des biens" },
        { src: "/images/showcase/loyers-with-button.png", title: "Suivi des loyers" },
        { src: "/images/showcase/fiche-identite.png", title: "Associés" },
        { src: "/images/showcase/finances-consolidated.png", title: "Vue financière" },
        { src: "/images/showcase/onboarding-step1.png", title: "Onboarding" },
    ];

    function openLightbox(index: number) {
        trackEvent(EVENTS.LANDING_LIGHTBOX_OPEN, { image: index });
        lightboxIndex = index;
        lightboxOpen = true;
    }

    function closeLightbox() {
        lightboxOpen = false;
    }

    function nextImage() {
        lightboxIndex = (lightboxIndex + 1) % allImages.length;
    }

    function prevImage() {
        lightboxIndex = (lightboxIndex - 1 + allImages.length) % allImages.length;
    }

    async function createGuestCheckout(planKey: string) {
        checkoutLoading = planKey;
        try {
            const res = await fetch(`${API_URL}/api/v1/stripe/create-guest-checkout`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ plan_key: planKey, billing_period: billingPeriod })
            });
            const data = await res.json();
            if (data.url) {
                window.location.href = data.url;
            }
        } catch {
            window.location.href = `/register?plan=${planKey}`;
        } finally {
            checkoutLoading = null;
        }
    }

    async function openCheckoutModal(planKey: string) {
        trackEvent(EVENTS.LANDING_PLAN_SELECT, { plan: planKey });
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) {
            goto(`/register?plan=${planKey}`);
            return;
        }
        const plan = PLANS_LIST.find((p: any) => p.key === planKey);
        if (!plan) return;
        modalPlanKey = planKey;
        modalPlanName = plan.name;
        modalPlanPrice = billingPeriod === 'month' ? `${plan.monthlyPrice}€` : `${plan.yearlyPrice}€`;
        modalPlanPeriod = billingPeriod === 'month' ? "/mois" : "/an";
        modalPlanFeatures = plan.features;
        modalOpen = true;
    }

    function handleModalConfirm() {
        modalOpen = false;
        createGuestCheckout(modalPlanKey);
    }
</script>

<!-- Checkout Modal -->
<CheckoutConfirmModal
    open={modalOpen}
    planKey={modalPlanKey}
    planName={modalPlanName}
    planPrice={modalPlanPrice}
    planPeriod={modalPlanPeriod}
    planFeatures={modalPlanFeatures}
    loading={checkoutLoading !== null}
    onCancel={() => modalOpen = false}
    onConfirm={handleModalConfirm}
/>


<!-- Sections Landing -->
<HeroSection />
<FeaturesSection />
<CommentCaMarcheSection bind:demoScene />
<TargetAudienceSection />
<ValueStackSection />
    <PricingSection
    plans={PLANS_LIST}
    bind:billingPeriod
    {checkoutLoading}
    {openCheckoutModal}
/>
<GuaranteeSection />
<CTASection />
<FAQSection bind:openFaqIndex />

{#if lightboxOpen}
    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
    <div
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm"
        onclick={closeLightbox}
        onkeydown={(e) => {
            if (e.key === 'Escape') closeLightbox();
            if (e.key === 'ArrowRight') nextImage();
            if (e.key === 'ArrowLeft') prevImage();
        }}
        role="dialog"
        aria-modal="true"
        aria-label="Galerie d'images"
        tabindex="-1"
    >
        <button onclick={closeLightbox} class="absolute top-6 right-6 text-white/80 hover:text-white z-10" aria-label="Fermer">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
        <button onclick={(e) => { e.stopPropagation(); prevImage(); }} class="absolute left-4 top-1/2 -translate-y-1/2 text-white/70 hover:text-white p-2" aria-label="Image precedente">
            <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
        </button>
        <!-- svelte-ignore a11y_click_events_have_key_events -->
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div onclick={(e) => e.stopPropagation()} class="max-w-[90vw] max-h-[85vh]">
            <img
                src={allImages[lightboxIndex].src}
                alt={allImages[lightboxIndex].title}
                class="max-w-full max-h-[80vh] rounded-lg shadow-2xl"
            />
            <div class="mt-3 text-center">
                <p class="text-white/90 font-medium">{allImages[lightboxIndex].title}</p>
                <p class="text-white/50 text-sm">{lightboxIndex + 1} / {allImages.length}</p>
            </div>
        </div>
        <button onclick={(e) => { e.stopPropagation(); nextImage(); }} class="absolute right-4 top-1/2 -translate-y-1/2 text-white/70 hover:text-white p-2" aria-label="Image suivante">
            <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
        </button>
    </div>
{/if}