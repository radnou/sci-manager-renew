#!/usr/bin/env python3
"""
Stripe Products Management - Setup for SCI-Manager Plans
"""
import os
import sys
import stripe
from dotenv import load_dotenv

# Load environment
load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

PLANS = {
    "starter": {
        "name": "Starter",
        "price": 1900,  # €19.00
        "currency": "eur",
        "billing_period": "month",
        "features": ["5 biens max", "Gestion loyers de base", "Quitus PDF", "Support email"],
        "description": "Plan idéal pour débuter avec votre gestion SCI"
    },
    "pro": {
        "name": "Pro",
        "price": 4900,  # €49.00
        "currency": "eur",
        "billing_period": "month",
        "features": ["Biens illimités", "Gestion complète loyers/charges", "Cerfa 2044 auto", "Quitus numérotés", "Support prioritaire", "Import/export données"],
        "description": "Plan complet pour les investisseurs SCI professionnels"
    },
    "lifetime": {
        "name": "Lifetime",
        "price": 29900,  # €299.00
        "currency": "eur",
        "billing_period": "once",
        "features": ["Accès à vie", "Toutes fonctionnalités Pro", "Mises à jour illimitées", "Support prioritaire à vie"],
        "description": "Achat unique - Licence à vie sans renouvellement"
    }
}

def check_existing_products():
    """Check for existing SCI-Manager products"""
    print("🔍 Vérification des produits Stripe existants...")
    products = stripe.Product.list(limit=100)
    
    existing = {}
    for product in products.data:
        if "sci" in product.name.lower() or any(plan in product.name.lower() for plan in ["starter", "pro", "lifetime"]):
            existing[product.name.lower()] = product
            print(f"  ✅ Trouvé: {product.name} (ID: {product.id})")
    
    return existing

def create_product_with_price(plan_key, plan_data, existing):
    """Create or update a product and its price"""
    plan_name = plan_data["name"]
    
    # Check if already exists
    existing_key = plan_name.lower()
    if existing_key in existing:
        product = existing[existing_key]
        print(f"  ℹ️  Produit existant: {plan_name} (ID: {product.id})")
        
        # Check for prices
        prices = stripe.Price.list(product=product.id)
        if prices.data:
            for price in prices.data:
                print(f"      └─ Prix: {price.unit_amount/100:.2f} {price.currency.upper()} ({price.billing_period if price.billing_period else 'once'})")
        return product, prices.data[0] if prices.data else None
    
    # Create new product
    print(f"  ✨ Création du produit: {plan_name}...")
    
    product = stripe.Product.create(
        name=f"SCI-Manager - {plan_data['name']}",
        description=plan_data["description"],
        type="service",
        metadata={
            "plan_type": plan_key,
            "billing_period": plan_data["billing_period"],
            "features": ", ".join(plan_data["features"])
        }
    )
    
    print(f"     └─ Produit créé: {product.id}")
    
    # Create price
    if plan_data["billing_period"] == "month":
        price = stripe.Price.create(
            product=product.id,
            unit_amount=plan_data["price"],
            currency=plan_data["currency"],
            recurring={
                "interval": "month",
                "usage_type": "licensed"
            }
        )
    else:  # lifetime/once
        price = stripe.Price.create(
            product=product.id,
            unit_amount=plan_data["price"],
            currency=plan_data["currency"]
        )
    
    print(f"     └─ Prix créé: {plan_data['price']/100:.2f} {plan_data['currency'].upper()}")
    
    return product, price

def main():
    print("\n" + "="*70)
    print("     🚀 SCI-Manager Stripe Setup - Création des Plans Tarifaires")
    print("="*70 + "\n")
    
    try:
        # Check existing
        existing = check_existing_products()
        print()
        
        # Create/update products
        products_info = {}
        for plan_key, plan_data in PLANS.items():
            product, price = create_product_with_price(plan_key, plan_data, existing)
            if product and price:
                products_info[plan_key] = {
                    "product_id": product.id,
                    "price_id": price.id,
                    "product_name": product.name,
                    "price_amount": plan_data["price"] / 100,
                    "currency": plan_data["currency"]
                }
        
        # Display summary
        print("\n" + "="*70)
        print("     ✅ RÉSUMÉ - Produits Stripe Configurés")
        print("="*70)
        
        for plan_key, info in products_info.items():
            print(f"\n  📦 {info['product_name']}")
            print(f"     Product ID: {info['product_id']}")
            print(f"     Price ID:   {info['price_id']}")
            print(f"     Prix:       {info['price_amount']:.2f} {info['currency'].upper()}")
        
        # Export environment variables
        print("\n" + "="*70)
        print("     📝 À Ajouter au .env (Frontend)")
        print("="*70 + "\n")
        
        for plan_key, info in products_info.items():
            env_key = f"VITE_STRIPE_{plan_key.upper()}_PRICE_ID"
            print(f"{env_key}={info['price_id']}")
        
        # Backend config
        print("\n" + "="*70)
        print("     📝 À Ajouter au .env (Backend)")
        print("="*70 + "\n")
        
        for plan_key, info in products_info.items():
            env_key = f"STRIPE_{plan_key.upper()}_PRICE_ID"
            print(f"{env_key}={info['price_id']}")
        
        print("\n✅ Configuration Stripe terminée!\n")
        
    except stripe.error.StripeError as e:
        print(f"❌ Erreur Stripe: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
