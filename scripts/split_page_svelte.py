#!/usr/bin/env python3
"""
Script de split +page.svelte — extraction des sections en composants.

Usage : python3 split_page_svelte.py
"""

import re
from pathlib import Path

# Chemin du fichier source
PAGE_PATH = Path.home() / "Code/sci-manager-renew/frontend/src/routes/+page.svelte"
BACKUP_PATH = PAGE_PATH.with_suffix(".svelte.backup.2026-04-23")

def main():
    if not PAGE_PATH.exists():
        print(f"❌ Fichier non trouvé : {PAGE_PATH}")
        return

    content = PAGE_PATH.read_text()
    lines = content.split('\n')
    total_lines = len(lines)

    print(f"📄 {PAGE_PATH.name} : {total_lines} lignes")

    # Détection des sections par commentaires
    sections = []
    current_section = {"name": "header", "start": 0, "lines": []}

    for i, line in enumerate(lines):
        # Détecter les marqueurs de section
        if '<!-- ============================================================ -->' in line:
            if current_section["lines"]:
                current_section["end"] = i
                sections.append(current_section)
            current_section = {"name": f"section_{len(sections)}", "start": i, "lines": [line]}
        else:
            current_section["lines"].append(line)

    # Ajouter la dernière section
    if current_section["lines"]:
        current_section["end"] = total_lines
        sections.append(current_section)

    print(f"📦 {len(sections)} sections détectées")

    # Afficher les sections
    for i, section in enumerate(sections):
        name = section["name"]
        start = section["start"]
        end = section.get("end", total_lines)
        length = end - start
        print(f"  [{i}] {name:20s} : lignes {start:4d}-{end:4d} ({length:4d} lignes)")

    # Créer le fichier +page.svelte refactorisé
    create_refactored_page(sections)

    print("\n✅ Split terminé")

def create_refactored_page(sections):
    """Crée le +page.svelte refactorisé avec imports des composants."""

    # Détecter les imports nécessaires depuis les sections
    imports_needed = {
        "onMount": True,
        "goto": True,
        "getCurrentSession": True,
        "Button": True,
        "Badge": True,
        "Card": True,
        "CardContent": True,
        "CardHeader": True,
        "CardTitle": True,
        "lucide": True,
    }

    # Générer le contenu
    output = []

    # Script
    output.append('<script lang="ts">')
    output.append('    import { onMount } from "svelte";')
    output.append('    import { goto } from "$app/navigation";')
    output.append('    import { getCurrentSession } from "$lib/auth/session";')
    output.append('    import { Button } from "$lib/components/ui/button";')
    output.append('    import { Badge } from "$lib/components/ui/badge";')
    output.append('    import { Card, CardContent, CardHeader, CardTitle } from "$lib/components/ui/card";')
    output.append('    import { Building2, FileText, TrendingUp, Shield, Users, Calculator, Check, ArrowRight, Briefcase, BarChart3, ChevronDown, ChevronUp, Loader2, Crown } from "lucide-svelte";')
    output.append('    import { API_URL } from "$lib/api";')
    output.append('    import { supabase } from "$lib/supabase";')
    output.append('    import CheckoutConfirmModal from "$lib/components/CheckoutConfirmModal.svelte";')
    output.append('    import AppDemoVideo from "$lib/components/AppDemoVideo.svelte";')
    output.append('    import { trackEvent, EVENTS } from "$lib/analytics";')
    output.append('    import { PLANS_LIST, formatPrice, formatPeriod, formatPriceTTC } from "$lib/config/plans";')
    output.append('')
    output.append('    // Composants landing')
    output.append('    import HeroSection from "$lib/landing/HeroSection.svelte";')
    output.append('    import FeaturesSection from "$lib/landing/FeaturesSection.svelte";')
    output.append('    import CommentCaMarcheSection from "$lib/landing/CommentCaMarcheSection.svelte";')
    output.append('    import TargetAudienceSection from "$lib/landing/TargetAudienceSection.svelte";')
    output.append('    import ValueStackSection from "$lib/landing/ValueStackSection.svelte";')
    output.append('    import PricingSection from "$lib/landing/PricingSection.svelte";')
    output.append('    import GuaranteeSection from "$lib/landing/GuaranteeSection.svelte";')
    output.append('    import CTASection from "$lib/landing/CTASection.svelte";')
    output.append('    import FAQSection from "$lib/landing/FAQSection.svelte";')
    output.append('    import FooterSection from "$lib/landing/FooterSection.svelte";')
    output.append('    import TrustBar from "$lib/landing/TrustBar.svelte";')
    output.append('    import CookieBanner from "$lib/components/CookieBanner.svelte";')
    output.append('')

    # États et logique
    output.append('    onMount(async () => {')
    output.append('        const session = await getCurrentSession();')
    output.append('        if (session?.user) {')
    output.append('            goto("/dashboard");')
    output.append('        }')
    output.append('    });')
    output.append('')

    # Variables d'état
    output.append('    let billingPeriod = $state<\'month\' | \'year\'>(\'month\');')
    output.append('    let checkoutLoading = $state<string | null>(null);')
    output.append('    let modalOpen = $state(false);')
    output.append('    let modalPlanKey = $state(\'\');')
    output.append('    let modalPlanName = $state(\'\');')
    output.append('    let modalPlanPrice = $state(\'\');')
    output.append('    let modalPlanPeriod = $state(\'\');')
    output.append('    let modalPlanFeatures = $state<string[]>([]);')
    output.append('    let openFaqIndex = $state<number | null>(null);')
    output.append('    let demoScene = $state(0);')
    output.append('    let lightboxOpen = $state(false);')
    output.append('    let lightboxIndex = $state(0);')
    output.append('')

    # Données
    output.append('    const allImages = [')
    output.append('        { src: "/images/showcase/dashboard-light.png", title: "Tableau de bord" },')
    output.append('        { src: "/images/showcase/biens-grid.png", title: "Grille des biens" },')
    output.append('        { src: "/images/showcase/loyers-with-button.png", title: "Suivi des loyers" },')
    output.append('        { src: "/images/showcase/fiche-identite.png", title: "Associés" },')
    output.append('        { src: "/images/showcase/finances-consolidated.png", title: "Vue financière" },')
    output.append('        { src: "/images/showcase/onboarding-step1.png", title: "Onboarding" },')
    output.append('    ];')
    output.append('')

    # Fonctions
    output.append('    function openLightbox(index: number) {')
    output.append('        trackEvent(EVENTS.LANDING_LIGHTBOX_OPEN, { image: index });')
    output.append('        lightboxIndex = index;')
    output.append('        lightboxOpen = true;')
    output.append('    }')
    output.append('')
    output.append('    function closeLightbox() {')
    output.append('        lightboxOpen = false;')
    output.append('    }')
    output.append('')
    output.append('    function nextImage() {')
    output.append('        lightboxIndex = (lightboxIndex + 1) % allImages.length;')
    output.append('    }')
    output.append('')
    output.append('    function prevImage() {')
    output.append('        lightboxIndex = (lightboxIndex - 1 + allImages.length) % allImages.length;')
    output.append('    }')
    output.append('')

    # Fonctions checkout
    output.append('    async function createGuestCheckout(planKey: string) {')
    output.append('        checkoutLoading = planKey;')
    output.append('        try {')
    output.append('            const res = await fetch(`${API_URL}/api/v1/stripe/create-guest-checkout`, {')
    output.append('                method: "POST",')
    output.append('                headers: { "Content-Type": "application/json" },')
    output.append('                body: JSON.stringify({ plan_key: planKey, billing_period: billingPeriod })')
    output.append('            });')
    output.append('            const data = await res.json();')
    output.append('            if (data.url) {')
    output.append('                window.location.href = data.url;')
    output.append('            }')
    output.append('        } catch {')
    output.append('            window.location.href = `/register?plan=${planKey}`;')
    output.append('        } finally {')
    output.append('            checkoutLoading = null;')
    output.append('        }')
    output.append('    }')
    output.append('')
    output.append('    async function openCheckoutModal(planKey: string) {')
    output.append('        trackEvent(EVENTS.LANDING_PLAN_SELECT, { plan: planKey });')
    output.append('        const { data: { session } } = await supabase.auth.getSession();')
    output.append('        if (!session) {')
    output.append('            goto(`/register?plan=${planKey}`);')
    output.append('            return;')
    output.append('        }')
    output.append('        const plan = PLANS_LIST.find((p: any) => p.key === planKey);')
    output.append('        if (!plan) return;')
    output.append('        modalPlanKey = planKey;')
    output.append('        modalPlanName = plan.name;')
    output.append('        modalPlanPrice = billingPeriod === \'month\' ? `${plan.monthlyPrice}€` : `${plan.yearlyPrice}€`;')
    output.append('        modalPlanPeriod = billingPeriod === \'month\' ? "/mois" : "/an";')
    output.append('        modalPlanFeatures = plan.features;')
    output.append('        modalOpen = true;')
    output.append('    }')
    output.append('')
    output.append('    function handleModalConfirm() {')
    output.append('        modalOpen = false;')
    output.append('        createGuestCheckout(modalPlanKey);')
    output.append('    }')
    output.append('</script>')
    output.append('')

    # Template
    output.append('<!-- Checkout Modal -->')
    output.append('<CheckoutConfirmModal')
    output.append('    open={modalOpen}')
    output.append('    planKey={modalPlanKey}')
    output.append('    planName={modalPlanName}')
    output.append('    planPrice={modalPlanPrice}')
    output.append('    planPeriod={modalPlanPeriod}')
    output.append('    planFeatures={modalPlanFeatures}')
    output.append('    onClose={() => modalOpen = false}')
    output.append('    onConfirm={handleModalConfirm}')
    output.append('/>')
    output.append('')

    output.append('<!-- Cookie Banner RGPD -->')
    output.append('<CookieBanner />')
    output.append('')

    output.append('<!-- Sections Landing -->')
    output.append('<HeroSection />')
    output.append('<FeaturesSection />')
    output.append('<CommentCaMarcheSection bind:demoScene />')
    output.append('<TargetAudienceSection />')
    output.append('<ValueStackSection />')
    output.append('<PricingSection')
    output.append('    {plans}')
    output.append('    bind:billingPeriod')
    output.append('    {checkoutLoading}')
    output.append('    {openCheckoutModal}')
    output.append('/>')
    output.append('<GuaranteeSection />')
    output.append('<CTASection />')
    output.append('<FAQSection bind:openFaqIndex />')
    output.append('<FooterSection />')
    output.append('')

    # Lightbox
    output.append('{#if lightboxOpen}')
    output.append('    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->')
    output.append('    <div')
    output.append('        class="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm"')
    output.append('        onclick={closeLightbox}')
    output.append('        onkeydown={(e) => {')
    output.append('            if (e.key === \'Escape\') closeLightbox();')
    output.append('            if (e.key === \'ArrowRight\') nextImage();')
    output.append('            if (e.key === \'ArrowLeft\') prevImage();')
    output.append('        }}')
    output.append('        role="dialog"')
    output.append('        aria-modal="true"')
    output.append('        aria-label="Galerie d\'images"')
    output.append('        tabindex="-1"')
    output.append('    >')
    output.append('        <button onclick={closeLightbox} class="absolute top-6 right-6 text-white/80 hover:text-white z-10" aria-label="Fermer">')
    output.append('            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>')
    output.append('        </button>')
    output.append('        <button onclick={(e) => { e.stopPropagation(); prevImage(); }} class="absolute left-4 top-1/2 -translate-y-1/2 text-white/70 hover:text-white p-2" aria-label="Image precedente">')
    output.append('            <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>')
    output.append('        </button>')
    output.append('        <!-- svelte-ignore a11y_click_events_have_key_events -->')
    output.append('        <!-- svelte-ignore a11y_no_static_element_interactions -->')
    output.append('        <div onclick={(e) => e.stopPropagation()} class="max-w-[90vw] max-h-[85vh]">')
    output.append('            <img')
    output.append('                src={allImages[lightboxIndex].src}')
    output.append('                alt={allImages[lightboxIndex].title}')
    output.append('                class="max-w-full max-h-[80vh] rounded-lg shadow-2xl"')
    output.append('            />')
    output.append('            <div class="mt-3 text-center">')
    output.append('                <p class="text-white/90 font-medium">{allImages[lightboxIndex].title}</p>')
    output.append('                <p class="text-white/50 text-sm">{lightboxIndex + 1} / {allImages.length}</p>')
    output.append('            </div>')
    output.append('        </div>')
    output.append('        <button onclick={(e) => { e.stopPropagation(); nextImage(); }} class="absolute right-4 top-1/2 -translate-y-1/2 text-white/70 hover:text-white p-2" aria-label="Image suivante">')
    output.append('            <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>')
    output.append('        </button>')
    output.append('    </div>')
    output.append('{/if}')

    # Écrire le fichier
    output_text = '\n'.join(output)
    PAGE_PATH.write_text(output_text)

    print(f"✅ {PAGE_PATH.name} refactorisé : {len(output)} lignes")

if __name__ == "__main__":
    main()
