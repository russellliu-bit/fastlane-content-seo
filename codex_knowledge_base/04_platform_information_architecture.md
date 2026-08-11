# Platform Information Architecture

Status: draft
Owner: Russell
Last Updated: 2026-03-07
Scope: current state
Source of Truth: internal Shopify scan + business interpretation

## 1. Purpose
This document defines the current platform-level information architecture of Heyup based on internal backend structure, not only public-facing navigation.

## 2. Platform Definition
Heyup operates as a hybrid community-commerce platform that combines:
- product discovery
- tryout campaigns
- community participation
- editorial content
- affiliate and creator programs
- direct retail
- brand partnerships

## 3. Core System Layers
Heyup currently consists of the following interconnected layers:
- Product catalog layer
- Tryout / campaign layer
- Newsroom / editorial content layer
- Affiliate / ambassador / referral layer
- Community participation layer
- Brand layer
- Sales channel layer
- Marketing / automation layer

## 4. Core Platform Logic
The platform is not structured as a standard e-commerce catalog.
It is structured around a flywheel:

1. Users discover products
2. Users vote / wish / apply for tryouts
3. Selected testers receive products
4. Testers create reviews and feedback
5. Content and reviews drive trust and traffic
6. Affiliate and retail transactions monetize attention
7. Brand partnerships and launches add more products into the system

## 5. Primary Platform Surfaces
Observed primary surfaces include:
- Product discovery and collection pages
- Tryout landing pages
- Newsroom and blog channels
- Community / Discord / brand community channels
- Affiliate / ambassador / referral entry points
- Retail purchase surfaces
- Brand directory and brand-specific content

## 6. Strategic Interpretation
Heyup should be understood internally as a connected system where:
- products are the main entities
- tryouts are the trust-generation mechanism
- content is the explanation and discovery mechanism
- community is the participation mechanism
- commerce and affiliate systems are monetization layers

## 7. Implications for Future Projects
Every future project should identify:
- which core layer it belongs to
- which adjacent layers it depends on
- what product/community/content/commercial data it should reuse
