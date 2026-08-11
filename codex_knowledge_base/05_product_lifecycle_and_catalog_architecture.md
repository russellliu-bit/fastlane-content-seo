# Product Lifecycle and Catalog Architecture

Status: draft
Owner: Russell
Last Updated: 2026-03-07
Scope: current state
Source of Truth: internal Shopify scan

## 1. Purpose
This document defines the current product lifecycle model and catalog structure of Heyup.

## 2. Product as the Core Entity
Products are the primary objects that connect discovery, tryouts, reviews, community engagement, affiliate promotion, and retail.

## 3. Product Lifecycle System
The current lifecycle appears to include:

1. Wishing Phase
- Products can be liked or voted for by users
- Used to signal demand and interest

2. Tryout Phase
- Products enter active testing campaigns
- Users apply for tester slots

3. Reviewed Phase
- Tryouts are completed
- Community reviews and feedback become available

4. Closed Phase
- Campaign is archived
- Product remains part of historical catalog / content memory

5. Retail Phase
- Product is available for direct purchase or downstream commercial use

## 4. Product Category Structure
Observed categories include:
- Audio
- Smartphones & Tablets
- Wearables
- Smart Home
- Gaming Accessories
- Tech & Gadgets

## 5. Product Metadata and Custom Fields
Observed product-related custom fields include:
- tryout_tag
- target_number
- brand_intro
- tryout_steps
- upcoming_end_time
- review_button_link
- discount_info
- discount_code

## 6. Technical Product Attributes
Observed product specifications include examples such as:
- color
- connection type
- keyboard specs
- audio connectivity
- power source
- operating system

## 7. Brand-Catalog Relationship
Products are connected to brands through brand metaobjects.
This suggests that product pages, brand pages, collections, and tryout campaigns should share reusable brand-linked data.

## 8. Internal Interpretation
The current product model is richer than a normal Shopify catalog.
It behaves like a product participation model, where products can move through community, campaign, review, and commercial states.

## 9. Implications
- Future projects should treat lifecycle status as a first-class field
- Content systems should reuse lifecycle stages
- Topic hubs and filters should be able to segment products by lifecycle phase
- Product data design should support both editorial and commercial use cases
