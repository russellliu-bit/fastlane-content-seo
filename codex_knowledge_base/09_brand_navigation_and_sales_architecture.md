# Brand, Navigation, and Sales Architecture

Status: draft
Owner: Russell
Last Updated: 2026-03-07
Scope: current state
Source of Truth: internal Shopify scan

## 1. Purpose
This document summarizes the current brand layer, navigation layer, affiliate layer, and sales-channel layer of Heyup.

## 2. Brand Architecture
Heyup appears to use a brand metaobject system with fields such as:
- brand name
- logo
- introduction/story
- product categories
- website link
- community channel link
- related products

## 3. Brand Layer Functions
The brand system appears to power:
- brand directory navigation
- brand intros on product/campaign pages
- brand-specific collections
- Brand Buzz content
- partner and launch-related discovery

## 4. Featured Brand Examples
Observed brands include:
- REDMAGIC
- Nothing
- Nubia
- Redmi
- SHOKZ
- Haylou
- 1MORE
- Insta360
- EZVIZ
- Abxylute

## 5. Main Navigation Structure
Observed navigation includes:
- Tryouts
- Referral Program
- Brand Directory
- Newsroom
- Community / Discord
- Top Categories
- Monthly Tryouts
- Heyup Drop

## 6. Affiliate and Creator Commerce Layer
Observed affiliate structure includes:
- Shopify Collabs integration
- affiliate application flow
- creator invites
- tiered commission model
- personalized affiliate links and codes
- automatic tracking and payouts
- creator dashboard access

## 7. Sales Channels
Observed active channels include:
- Online Store
- Facebook & Instagram
- Shopify Inbox
- custom/private APIs

## 8. Supporting Technical and Marketing Infrastructure
Observed supporting tools include:
- Okendo
- Mailchimp
- Shopify Collabs
- Zapier
- Shopify Flow
- Launchpad
- LangShop
- Translate & Adapt
- Search & Discovery
- custom tools such as Fastgrowth Data Pipeline and Fastgrowth Events

## 9. Strategic Interpretation
Brand, navigation, community, content, and sales are tightly linked.
The platform is not only catalog-driven or content-driven; it is brand- and campaign-aware across navigation and monetization.

## 10. Implications
- Future topic hubs and landing pages should leverage brand metaobjects, not hardcoded brand data
- Affiliate initiatives should integrate with existing creator/ambassador infrastructure where possible
- Navigation should be redesigned around reusable entities rather than page-by-page manual logic
