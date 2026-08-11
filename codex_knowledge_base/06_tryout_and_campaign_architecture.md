# Tryout and Campaign Architecture

Status: draft
Owner: Russell
Last Updated: 2026-03-07
Scope: current state
Source of Truth: internal Shopify scan

## 1. Purpose
This document defines the current tryout and campaign architecture of Heyup.

## 2. Role of Tryouts
Tryouts are a core engagement and trust-building mechanism.
They are not just marketing campaigns; they are a structured product-testing workflow that connects community participation, review generation, and downstream commerce/content.

## 3. Current 4-Step Tryout Workflow
The observed workflow includes:

1. Cast Your Wish
- Users sign up and like products
- Interest and demand are collected

2. Apply for Tryout
- Users submit an application
- Community membership is required

3. Tester Announcement
- Winners are selected
- Announcements happen in the community

4. Test and Share
- Testers receive products
- Testers submit reviews and feedback

## 4. Tryout Infrastructure
Observed components include:
- Dedicated landing pages for each tryout
- Template system: tryout-page-template
- Metaobject-driven content
- Brand intro integration
- Steps/workflow integration
- Target tracking
- Review submission integration
- Eligibility requirements tied to community membership

## 5. Campaign Types and Examples
Observed examples include campaigns for:
- REDMAGIC 7S Pro
- Samsung Galaxy Z Fold 4
- Nothing Phone (1)
- DreameBot L10s Ultra
- Nothing Ear (1)
- seasonal campaigns such as Back to School

## 6. Campaign States
The system appears to support state distinctions such as:
- active tryout
- testing
- tested
- archived / closed

## 7. Why This Matters
Tryouts generate:
- demand signals
- participation signals
- review content
- social proof
- reusable commercial assets

## 8. Implications for Future Projects
- Tryout data should be reusable by content, SEO, affiliate, and store initiatives
- Campaign pages should not be treated as isolated microsites
- A normalized tryout entity model will be valuable for future automation and analytics
